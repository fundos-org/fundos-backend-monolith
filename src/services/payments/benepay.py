import os
import json
import base64
from datetime import datetime, timezone
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import httpx
from fastapi import HTTPException
import redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from src.logging.logging_setup import get_logger
from src.models.transaction import Transaction, TransactionType, TransactionStatus
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
        investment_id: str,
        amount: float,
        customer_name: str,
        customer_email: str,
        customer_phone: str,
        description: str,
        currency: str,
        expiry_in_minutes: int
    ) -> dict:
        """Generate the payment payload for BenePay API."""
        return {
            "merchantid": self.api_key,
            "transactionid": str(investment_id),
            "amount": str(amount),
            "currency": currency,
            "description": description,
            "payerName": customer_name,
            "payerEmail": customer_email,
            "payerMobile": customer_phone,
            "expiryInMinutes": str(expiry_in_minutes)
        }

    async def send_payment_url(
        self,
        session: AsyncSession,
        investment_id: str,
        amount: float,
        customer_name: str,
        customer_email: str,
        customer_phone: str,
        description: str = "Investment Payment",
        currency: str = "INR",
        expiry_in_minutes: int = 30
    ) -> str:
        """Initiate a payment request and return the payment URL."""
        auth_token = await self._get_auth_token()
        payload = self._get_payment_payload(
            investment_id, amount, customer_name, customer_email, customer_phone,
            description, currency, expiry_in_minutes
        )
        encrypted_payload = self._encrypt_data(payload)
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Header": self.api_key,
            "Content-Type": "application/json"
        }
        data = {"encryptedData": encrypted_payload}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.payment_request_url, headers=headers, json=data)
                response.raise_for_status()
                encrypted_response = base64.urlsafe_b64decode(response.json().get("encryptedData"))
                decrypted_response = self._decrypt_data(encrypted_response)

            transaction = Transaction(
                investment_id=investment_id,
                transaction_type=TransactionType.PAYMENT,
                order_id=str(investment_id),
                transaction_id=decrypted_response.get("transactionid"),
                amount=amount,
                currency=currency,
                description=description,
                status=TransactionStatus.PENDING,
                response_code=decrypted_response.get("response_code")
            )
            session.add(transaction)
            await session.commit()
            await session.refresh(transaction)
            logger.info(f"Payment initiated for transaction {transaction.transaction_id}")

            return decrypted_response.get("payment_url")

        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to initiate payment for investment_id {investment_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Payment initiation failed")
        except Exception as e:
            logger.error(f"Unexpected error for investment_id {investment_id}: {str(e)}")
            await session.rollback()
            raise HTTPException(status_code=500, detail="Internal server error")
    
    async def handle_webhook(
        self, 
        session: AsyncSession, 
        webhook_data: dict
    ) -> None:
        """Process incoming webhook data from BenePay."""
        try:
            encrypted_data = base64.urlsafe_b64decode(webhook_data.get("encryptedData"))
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