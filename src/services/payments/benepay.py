import os
import json
import base64
from typing import Any, Dict, List
from datetime import datetime, timedelta, timezone
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import httpx
from fastapi import HTTPException
import redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from src.models.investment import Investment, InvestmentStatus
from src.logging.logging_setup import get_logger
from src.models.transaction import Transaction, TransactionType, TransactionStatus
from src.models.deal import Deal
from src.models.user import User
from src.configs.benepay import benepay_configs
from src.configs.configs import redis_configs

logger = get_logger(__name__)

# initiate Configs variables
CLIENT_ID = benepay_configs.client_id
CLIENT_SECRET = benepay_configs.client_secret
BASE_URL = benepay_configs.base_url
AUTH_URL = benepay_configs.auth_url
PAY_URL = benepay_configs.pay_url
API_KEY = benepay_configs.api_key
ENCRYPTION_KEY = benepay_configs.encryption_key
COMMENTS = benepay_configs.comments
CHARGES = benepay_configs.charges
CHARGES_REASON = benepay_configs.charges_reason
RETURN_URL = benepay_configs.return_url
MERCHANT_ID = benepay_configs.merchant_id

# Initiate redis credentials
REDIS_HOST = redis_configs.redis_host
REDIS_PORT = redis_configs.redis_port
REDIS_DB = redis_configs.redis_db
CACHE_TTL = redis_configs.redis_cache_ttl  # 5 minutes in seconds, aligned with likely Digitap session timeout
RATE_LIMIT = redis_configs.redis_rate_limit

class PaymentService:
    def __init__(self):
        """Initialize the PaymentService with API credentials and base URL."""
        self.client_id = CLIENT_ID
        self.client_secret = CLIENT_SECRET
        self.base_url = BASE_URL
        self.payment_request_url = PAY_URL
        self.auth_url = AUTH_URL
        self.api_key = API_KEY
        self.auth_token = None
        self.charges = CHARGES
        self.charges_reason = CHARGES_REASON
        self.return_url = RETURN_URL
        self.comments = COMMENTS
        self.merchant_id = MERCHANT_ID

        self.payment_request_url = PAY_URL
        self.redis = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True
        )

    async def _get_auth_token(
        self
    ) -> None:
        """Fetch OAuth2 token from BenePay authentication endpoint or use cached token."""
        cache_key = f"auth_token:{self.client_id}"
        cached_token = self.redis.get(cache_key)
        
        if cached_token:
            self.auth_token = cached_token
            logger.info(f"Using cached auth token: {self.auth_token}")
            return self.auth_token

        auth_url = self.auth_url
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Cookie": "XSRF-TOKEN=bd4d51ed-8b16-4c39-99f2-0b7e15bcb92a"
        }
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(auth_url, headers=headers, data=data)
                response.raise_for_status()
                self.auth_token = response.json().get("access_token")
                logger.info(f"Successfully fetched auth token: {self.auth_token}")

                # Store in Redis
                self.redis.setex(cache_key, CACHE_TTL, self.auth_token)
                logger.info(f"Cached auth token for client_id: {self.client_id}, cache_key: {cache_key}")

                return self.auth_token
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to fetch auth token: {str(e)}")
            raise HTTPException(status_code=500, detail="Authentication failed")
        
    def _encrypt_data(
        self, 
        data: dict
    ) -> str:
        """Encrypt payment data using AES-GCM with the provided encryption key and return base64 encoded string."""
        encryption_key = bytes.fromhex(benepay_configs.encryption_key)  # Convert hex string to bytes
        iv = os.urandom(12)
        cipher = Cipher(algorithms.AES(encryption_key), modes.GCM(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(json.dumps(data).encode('utf-8')) + encryptor.finalize()
        combined = iv + ciphertext + encryptor.tag
        return base64.urlsafe_b64encode(combined).decode('utf-8')

    def _decrypt_data(
        self, 
        encrypted_data: str
    ) -> dict:
        """Decrypt base64 encoded encrypted data received from BenePay API."""
        encryption_key = bytes.fromhex(benepay_configs.encryption_key)  # Convert hex string to bytes
        combined = base64.urlsafe_b64decode(encrypted_data)
        iv = combined[:12]
        tag = combined[-16:]
        ciphertext = combined[12:-16]
        cipher = Cipher(algorithms.AES(encryption_key), modes.GCM(iv, tag), backend=default_backend())
        decryptor = cipher.decryptor()
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        return json.loads(plaintext.decode('utf-8'))

    def _get_payment_payload(
        self,
        user: User,
        deal: Deal, 
        amount: float
    ) -> Dict[str, Any]:
        """Generate the payment payload for BenePay API."""

        # Define the payment payload variables
        current_date: str = datetime.now(timezone(timedelta(hours=5, minutes=30))).date().isoformat()
        collectionAmountCurrency: str = "INR"
        collectionReferenceNumber: str = f"{user.id}-{deal.id}-{current_date}"
        debtorEmailId: str = user.email, 
        debtorName: str = user.full_name,
        finalDueAmount: str = amount.__str__()
        requestorTransactionId: str = "0655097f-b6df-4984-96bf9c651fb32f8d"
        debtorMobileNumber: str = user.phone_number
        debtorWhatsAppNumber: str = user.phone_number
        reasonForCollection: str = "OnlinePayment"
        initialDueAmount: str = amount.__str__()
        charges: str = self.charges.__str__()
        reasonForCharges: str = self.charges_reason 
        finalDueDate: str = current_date
        additionalComments: str = self.comments
        payVia: List[str] = ["UI", "CC"]
        returnUrl: str = self.return_url
        merchantId: str = self.merchant_id

        payload: Dict = {
            "collectionAmountCurrency": collectionAmountCurrency,
            "collectionReferenceNumber": collectionReferenceNumber,
            "debtorEmailId": debtorEmailId,
            "debtorName": debtorName,
            "finalDueAmount": finalDueAmount,
            "requestorTransactionId": requestorTransactionId,
            "debtorMobileNumber": debtorMobileNumber,
            "debtorWhatsAppNumber": debtorWhatsAppNumber,
            "reasonForCollection": reasonForCollection,
            "initialDueAmount": initialDueAmount,
            "charges": charges,
            "reasonForCharges": reasonForCharges,
            "finalDueDate": finalDueDate,
            "additionalComments": additionalComments,
            "payVia": payVia,
            "returnUrl": returnUrl,
            "merchantId": merchantId
        }
        return payload

    async def _create_investment_and_transaction(
        self,
        user: User,
        deal: Deal,
        amount: float,
        idempotency_key: str,
        session: AsyncSession
    ) -> tuple[Investment, Transaction, dict]:
        # Check if a transaction is already active
        if session.in_transaction():
            # No need to start a new transaction
            investment = Investment(
                investor_id=user.id,
                deal_id=deal.id,
                amount=amount,
                status=InvestmentStatus.PENDING,
            )
            session.add(investment)
            await session.flush()  # Get investment.id

            transaction = Transaction(
                investment_id=investment.id,
                user_id=user.id,
                deal_id=deal.id,
                status=TransactionStatus.PENDING,
                amount=amount,
                type=TransactionType.PAYMENT,
                idempotency_key=idempotency_key
            )
            session.add(transaction)
            await session.flush()  # Get transaction.id
        else:
            # Start a new transaction if none exists
            async with session.begin():  # Full ACID
                investment = Investment(
                    user_id=user.id,
                    deal_id=deal.id,
                    amount=amount,
                    status=InvestmentStatus.PENDING,
                )
                session.add(investment)
                await session.flush()  # Get investment.id

                transaction = Transaction(
                    investment_id=investment.id,
                    user_id=user.id,
                    deal_id=deal.id,
                    status=TransactionStatus.PENDING,
                    amount=amount,
                    type=TransactionType.PAYMENT,
                    idempotency_key=idempotency_key
                )
                session.add(transaction)
                await session.flush()  # Get transaction.id

        return investment, transaction
    
    async def send_payment_url(
        self,
        session: AsyncSession,
        user_id: str,
        deal_id: str,
        amount: float, 
        idempotency_key: str
    ) -> str:
        """Initiate a payment request and return the payment URL."""

        # Check if request has already been processed
        stmt = select(Transaction).where(Transaction.idempotency_key == idempotency_key)
        existing = await session.execute(stmt)
        existing_txn = existing.scalar_one_or_none()

        if existing_txn:
            # Return previous payment URL or info if already sent
            return existing_txn.payment_url  # Assuming you store it
        
        auth_token = await self._get_auth_token()

        user: User = await session.get(User, user_id)
        deal: Deal = await session.get(Deal, deal_id)

        investment, transaction = await self._create_investment_and_transaction(
            user=user, 
            deal=deal, 
            amount=amount, 
            idempotency_key=idempotency_key,
            session=session
        )

        payload = self._get_payment_payload(user, deal, amount) #  get payload
        encrypted_payload = self._encrypt_data(payload) # encrypt payload
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Header": self.api_key,
            "Content-Type": "application/json"
        }
        data = {"encryptedData": encrypted_payload}

        try:
            async with httpx.AsyncClient() as client:
                response: Dict[str, Any] = await client.post(self.payment_request_url, headers=headers, json=data)
                response.raise_for_status()

                if response.get("statusCode") != 302:
                    raise HTTPException(status_code=response.get("statusCode"), detail=response.get("message"))

                if response.get("statusCode") == 302: 
                    transaction.payment_url = response.get("message")

            await session.commit()
            return response

        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to initiate payment for user_id: {user_id}, deal_id: {deal_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Payment initiation failed")
        except Exception as e:
            logger.error(f"Unexpected error for user_id: {user_id}, deal_id: {deal_id}  : {str(e)}")
            await session.rollback()
            raise HTTPException(status_code=500, detail="Internal server error")
        except ValueError as ve: 
            logger.error(f"Failed to initiate payment for user_id: {user_id}, deal_id: {deal_id}: {str(ve)}")
            raise HTTPException(status_code=500, detail="Payment initiation failed")
    
    async def handle_webhook(
        self, 
        session: AsyncSession, 
        webhook_data: str
    ) -> None:
        """Process incoming webhook data from BenePay."""
        try:
            encrypted_data = base64.urlsafe_b64decode(webhook_data)
            decrypted_data = self._decrypt_data(encrypted_data)

            logger.info(f"Received webhook data: {decrypted_data}")

            return {"status": "success"}
            
            statement = select(Transaction).where(
                Transaction.transaction_id == decrypted_data.get("transactionid"),
                Transaction.transaction_type == TransactionType.PAYMENT
            )
            result = await session.execute(statement)
            transaction = result.scalar_one_or_none()
            if not transaction:
                logger.error(f"Transaction not found for transaction_id {decrypted_data.get('transactionid')}")
                raise HTTPException(status_code=404, detail="Transaction not found")

            status_map = {
                "SUCCESS": TransactionStatus.COMPLETED,
                "PENDING": TransactionStatus.PENDING,
                "FAILED": TransactionStatus.FAILED
            }
            transaction.status = status_map.get(decrypted_data.get("status"), TransactionStatus.FAILED)
            transaction.updated_at = datetime.now(timezone.utc)
            session.add(transaction)
            await session.commit()
            await session.refresh(transaction)
            logger.info(f"Webhook processed for transaction {transaction.transaction_id}, status: {transaction.status}")

        except Exception as e:
            logger.error(f"Failed to process webhook: {str(e)}")
            await session.rollback()
            raise HTTPException(status_code=500, detail="Webhook processing failed")