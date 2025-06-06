import hashlib
import uuid
from typing import AnyStr
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
import httpx
from datetime import datetime, timezone
from src.logging.logging_setup import get_logger
from src.models.transaction import Transaction, TransactionType, TransactionStatus
from src.configs.configs import payment_configs
import json

logger = get_logger(__name__)

class PaymentService:
    def __init__(
        self,
        api_key: str = payment_configs.api_key,
        salt: str = payment_configs.salt,
        base_url: str = payment_configs.base_url 
    ):
        self.api_key = api_key
        self.salt = salt
        self.base_url = base_url
        self.payment_request_url = f"{base_url}/v2/getpaymentrequesturl"
        self.payment_status_url = f"{base_url}/v2/paymentstatus"
        self.refund_request_url = f"{base_url}/v2/refundrequest"
        self.refund_status_url = f"{base_url}/v2/refundstatus"

    def _generate_hash(self, params: dict) -> AnyStr:
        sorted_keys = sorted(params.keys())
        hash_data = self.salt + "|" + "|".join(str(params[key]) for key in sorted_keys if params[key])
        return hashlib.sha512(hash_data.encode()).hexdigest().upper()

    def _validate_response_hash(self, response_data: dict) -> bool:
        if "hash" not in response_data:
            logger.warning("No hash in response data")
            return False
        response_hash = response_data.pop("hash")
        sorted_keys = sorted(response_data.keys())
        hash_data = self.salt + "|" + "|".join(str(response_data[key]) for key in sorted_keys if response_data[key])
        calculated_hash = hashlib.sha512(hash_data.encode()).hexdigest().upper()
        return response_hash == calculated_hash

    async def create_payment(
        self,
        session: AsyncSession,
        investment_id: uuid.UUID,
        amount: float,
        customer_name: str,
        customer_email: str,
        customer_phone: str,
        description: str = "Investment Payment",
        currency: str = "INR",
        expiry_in_minutes: int = 30
    ) -> str:
        params = {
            "api_key": self.api_key,
            "order_id": str(investment_id),
            "amount": str(amount),
            "currency": currency,
            "description": description,
            "name": customer_name,
            "email": customer_email,
            "phone": customer_phone,
            "city": "Unknown",
            "country": "IND",
            "zip_code": "000000",
            "expiry_in_minutes": str(expiry_in_minutes)
        }
        params["hash"] = self._generate_hash(params)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.payment_request_url, data=params)
                response.raise_for_status()
                response_data = response.json()

            if not self._validate_response_hash(response_data.copy()):
                logger.error(f"Hash validation failed for order_id {investment_id}")
                raise HTTPException(status_code=500, detail="Invalid response hash from payment gateway")

            if response_data.get("response_code") != 0:
                logger.error(f"Payment request failed: {response_data.get('error_desc', 'Unknown error')}")
                raise HTTPException(status_code=500, detail=f"Payment request failed: {response_data.get('error_desc', 'Unknown error')}")

            transaction = Transaction(
                investment_id=investment_id,
                transaction_type=TransactionType.PAYMENT,
                order_id=str(investment_id),
                transaction_id=response_data.get("transaction_id"),
                amount=amount,
                currency=currency,
                description=description,
                status=TransactionStatus.PENDING,
                response_code=response_data.get("response_code")
            )
            session.add(transaction)
            await session.commit()
            await session.refresh(transaction)

            return response_data.get("payment_url")

        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to create payment for order_id {investment_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to connect to payment gateway")
        except Exception as e:
            logger.error(f"Unexpected error creating payment for order_id {investment_id}: {str(e)}")
            await session.rollback()
            raise HTTPException(status_code=500, detail="Internal server error")

    async def handle_webhook(
        self,
        session: AsyncSession,
        webhook_data: dict
    ) -> None:
        try:
            if not self._validate_response_hash(webhook_data.copy()):
                logger.error(f"Webhook hash validation failed for transaction_id {webhook_data.get('transaction_id')}")
                raise HTTPException(status_code=400, detail="Invalid webhook hash")

            order_id = webhook_data.get("order_id")
            transaction_id = webhook_data.get("transaction_id")
            response_code = webhook_data.get("response_code")

            status_map = {
                0: TransactionStatus.COMPLETED,
                1006: TransactionStatus.ON_HOLD,
            }
            status = status_map.get(response_code, TransactionStatus.FAILED)

            statement = select(Transaction).where(
                Transaction.order_id == order_id,
                Transaction.transaction_id == transaction_id,
                Transaction.transaction_type == TransactionType.PAYMENT
            )
            result = await session.execute(statement)
            transaction = result.scalar_one_or_none()
            if not transaction:
                logger.error(f"Transaction not found for order_id {order_id}, transaction_id {transaction_id}")
                raise HTTPException(status_code=404, detail="Transaction not found")

            transaction.status = status
            transaction.response_code = response_code
            transaction.payment_mode = webhook_data.get("payment_mode")
            transaction.refund_details = json.dumps(webhook_data.get("refund_details")) if webhook_data.get("refund_details") else None
            transaction.updated_at = datetime.now(timezone.utc)
            session.add(transaction)
            await session.commit()
            await session.refresh(transaction)

            logger.info(f"Updated transaction {transaction_id} with status {status}")

        except Exception as e:
            logger.error(f"Failed to process webhook for transaction_id {webhook_data.get('transaction_id')}: {str(e)}")
            await session.rollback()
            raise HTTPException(status_code=500, detail="Failed to process webhook")

    async def check_payment_status(
        self,
        session: AsyncSession,
        investment_id: uuid.UUID = None,
        transaction_id: str = None,
        page_number: int = 1,
        per_page: int = 10
    ) -> list[dict]:
        params = {
            "api_key": self.api_key,
            "page_number": str(page_number),
            "per_page": str(min(per_page, 50))
        }
        if investment_id:
            params["order_id"] = str(investment_id)
        if transaction_id:
            params["transaction_id"] = transaction_id
        params["hash"] = self._generate_hash(params)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.payment_status_url, data=params)
                response.raise_for_status()
                response_data = response.json()

            if not self._validate_response_hash(response_data.copy()):
                logger.error(f"Hash validation failed for payment status check: investment_id={investment_id}, transaction_id={transaction_id}")
                raise HTTPException(status_code=500, detail="Invalid response hash from payment gateway")

            if response_data.get("response_code") != 0:
                logger.error(f"Payment status check failed: {response_data.get('error_desc', 'Unknown error')}")
                raise HTTPException(status_code=500, detail=f"Payment status check failed: {response_data.get('error_desc', 'Unknown error')}")

            transactions = response_data.get("transactions", [])
            if investment_id and transactions:
                statement = select(Transaction).where(
                    Transaction.investment_id == investment_id,
                    Transaction.transaction_id == transactions[0].get("transaction_id"),
                    Transaction.transaction_type == TransactionType.PAYMENT
                )
                result = await session.execute(statement)
                transaction = result.scalar_one_or_none()
                if transaction:
                    status_map = {
                        0: TransactionStatus.COMPLETED,
                        1006: TransactionStatus.ON_HOLD,
                    }
                    transaction.status = status_map.get(transactions[0].get("response_code"), TransactionStatus.FAILED)
                    transaction.payment_mode = transactions[0].get("payment_mode")
                    transaction.refund_details = json.dumps(transactions[0].get("refund_details")) if transactions[0].get("refund_details") else None
                    transaction.response_code = transactions[0].get("response_code")
                    transaction.updated_at = datetime.now(timezone.utc)
                    session.add(transaction)
                    await session.commit()
                    await session.refresh(transaction)

            return transactions

        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to check payment status: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to connect to payment gateway")
        except Exception as e:
            logger.error(f"Unexpected error checking payment status: {str(e)}")
            await session.rollback()
            raise HTTPException(status_code=500, detail="Internal server error")

    async def initiate_refund(
        self,
        session: AsyncSession,
        investment_id: uuid.UUID,
        amount: float,
        description: str = "Refund for investment",
        merchant_refund_id: str = None
    ) -> dict:
        statement = select(Transaction).where(
            Transaction.investment_id == investment_id,
            Transaction.transaction_type == TransactionType.PAYMENT,
            Transaction.status == TransactionStatus.COMPLETED
        )
        result = await session.execute(statement)
        payment_transaction = result.scalar_one_or_none()
        if not payment_transaction:
            raise HTTPException(status_code=404, detail="Completed payment transaction not found")

        params = {
            "api_key": self.api_key,
            "transaction_id": payment_transaction.transaction_id,
            "amount": str(amount),
            "description": description
        }
        if merchant_refund_id:
            params["merchant_refund_id"] = merchant_refund_id
        params["hash"] = self._generate_hash(params)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.refund_request_url, data=params)
                response.raise_for_status()
                refund_data = response.json()

            if not self._validate_response_hash(refund_data.copy()):
                logger.error(f"Hash validation failed for refund: investment_id={investment_id}")
                raise HTTPException(status_code=500, detail="Invalid response hash from payment gateway")

            if refund_data.get("response_code") != 0:
                logger.error(f"Refund request failed: {refund_data.get('error_desc', 'Unknown error')}")
                raise HTTPException(status_code=500, detail=f"Refund request failed: {refund_data.get('error_desc', 'Unknown error')}")

            refund_transaction = Transaction(
                investment_id=investment_id,
                transaction_type=TransactionType.REFUND,
                order_id=str(investment_id),
                transaction_id=payment_transaction.transaction_id,
                refund_id=refund_data.get("refund_id"),
                amount=amount,
                currency=payment_transaction.currency,
                description=description,
                refund_amount=refund_data.get("refund_amount"),
                refund_status=refund_data.get("refund_status"),
                status=TransactionStatus.PENDING,
                response_code=refund_data.get("response_code")
            )
            session.add(refund_transaction)
            await session.commit()
            await session.refresh(refund_transaction)

            status_params = {
                "api_key": self.api_key,
                "transaction_id": payment_transaction.transaction_id,
                "refund_id": refund_data.get("refund_id"),
                "hash": ""
            }
            status_params["hash"] = self._generate_hash(status_params)

            async with httpx.AsyncClient() as client:
                status_response = await client.post(self.refund_status_url, data=status_params)
                status_response.raise_for_status()
                status_data = status_response.json()

            if not self._validate_response_hash(status_data.copy()):
                logger.error(f"Hash validation failed for refund status: investment_id={investment_id}")
                raise HTTPException(status_code=500, detail="Invalid response hash from payment gateway")

            if status_data.get("response_code") != 0:
                logger.error(f"Refund status check failed: {status_data.get('error_desc', 'Unknown error')}")
                raise HTTPException(status_code=500, detail=f"Refund status check failed: {status_data.get('error_desc', 'Unknown error')}")

            refund_transaction.refund_status = status_data.get("refund_status")
            refund_transaction.status = TransactionStatus.COMPLETED if status_data.get("refund_status") == "SUCCESS" else TransactionStatus.PENDING
            refund_transaction.updated_at = datetime.now(timezone.utc)
            session.add(refund_transaction)
            await session.commit()
            await session.refresh(refund_transaction)

            return status_data

        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to process refund for investment_id {investment_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to connect to payment gateway")
        except Exception as e:
            logger.error(f"Unexpected error processing refund for investment_id {investment_id}: {str(e)}")
            await session.rollback()
            raise HTTPException(status_code=500, detail="Internal server error")