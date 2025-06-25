import re
import httpx
import base64
import redis
import json
import os
from fastapi import HTTPException
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.kyc import KYC
from src.models.user import User
from src.logging.logging_setup import get_logger
from datetime import datetime
from src.configs.configs import redis_configs
from src.configs.configs import digitap_configs

# Configure logging
logger = get_logger(__name__)

DIGITAP_BASE_URL = digitap_configs.digitap_base_url
VALIDATION_BASE_URL = digitap_configs.validation_base_url
UAT_BASE_URL = digitap_configs.ukyc_uat_base_url
CLIENT_ID = digitap_configs.uat_client_id  # Use the UAT client_id
CLIENT_SECRET = digitap_configs.uat_client_secret  # Use the UAT client_secret
REDIS_HOST = redis_configs.redis_host
REDIS_PORT = redis_configs.redis_port
REDIS_DB = redis_configs.redis_db
CACHE_TTL = redis_configs.redis_cache_ttl  # 5 minutes in seconds, aligned with likely Digitap session timeout

class UnifiedKycService:
    def __init__(self):
        self.base_url = DIGITAP_BASE_URL
        self.validation_base_url = VALIDATION_BASE_URL
        self.uat_base_url = UAT_BASE_URL
        self.client_id = CLIENT_ID
        self.client_secret = CLIENT_SECRET
        self.redis = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True
        )

    def get_auth_header_basic(self) -> dict:
        token = f"{self.client_id}:{self.client_secret}"
        base64_token = base64.b64encode(token.encode()).decode()
        return {
            "Authorization": f"Basic {base64_token}",
            "Content-Type": "application/json"
        }

    def _get_cache_key(self, unique_id: str) -> str:
        return f"kyc:unified:{unique_id}"

    def _get_rate_limit_key(self, user_id: str | UUID) -> str:
        return f"kyc:rate_limit:{str(user_id)}"

    def _generate_unique_id(self, user_id: str) -> str:
        """Generate a unique ID by combining user_id with a timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"{user_id}_{timestamp}"

    async def send_kyc_request(
        self, 
        user_id: str,
        session: AsyncSession  # Added session parameter for consistency
    ) -> dict:
        try:
            # Validate user_id as UUID
            UUID(user_id)
        except ValueError:
            logger.error(f"Invalid user_id format: {user_id}")
            raise HTTPException(status_code=400, detail="Invalid user_id format")

        # Check rate limit (60-second interval)
        rate_limit_key = self._get_rate_limit_key(user_id)
        if self.redis.get(rate_limit_key):
            logger.error(f"KYC request rate limit exceeded for user_id: {user_id}")
            raise HTTPException(status_code=429, detail="Please wait 60 seconds before requesting a new KYC URL")

        # Generate unique ID for Digitap API
        unique_id = self._generate_unique_id(user_id)

        url = f"{self.uat_base_url}/kyc-unified/v1/generate-url/"
        payload = {
            "redirectionUrl": "https://api.fundos.services",
            "uniqueId": unique_id,
            "expiryHours": 72
        }
        headers = self.get_auth_header_basic()

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)

        if response.status_code != 200:
            logger.error(f"Failed to generate unified KYC URL: {response.status_code} {response.text}")
            raise HTTPException(status_code=response.status_code, detail=response.text)

        data = response.json()
        if data.get("code") != "200":
            error_msg = data.get("msg", "Failed to generate unified KYC URL")
            logger.error(f"Unified KYC URL generation failed: {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)

        model = data.get("model", {})
        transaction_id = model.get("unifiedTransactionId")  # Use correct field name from response

        cache_value = {
            "unified_transaction_id": transaction_id,
            "short_url": model.get("shortUrl"),
            "url": model.get("url"),
            "user_id": user_id,  # Store original user_id
            "unique_id": unique_id  # Store unique_id for cache retrieval
        }

        # Store in Redis with unique_id as part of the key
        cache_key = self._get_cache_key(unique_id)
        self.redis.setex(cache_key, CACHE_TTL, json.dumps(cache_value))
        # Set rate limit key (600 seconds as per your update)
        self.redis.setex(rate_limit_key, 600, "1")
        logger.info(f"Cached unified KYC data for user_id: {user_id}, unique_id: {unique_id}, cache_key: {cache_key}")

        return {
            "user_id": user_id,
            "success": True,
            "message": "Unified KYC URL generated successfully",
            "url": model.get("url"),
            "short_url": model.get("shortUrl")
        }

    async def get_kyc_details(
        self, 
        user_id: str, 
        session: AsyncSession
    ) -> dict:
        try:
            # Validate user_id as UUID
            UUID(user_id)
        except ValueError:
            logger.error(f"Invalid user_id format: {user_id}")
            raise HTTPException(status_code=400, detail="Invalid user_id format")

        # Find the cache key by searching for keys with user_id
        cache_key_pattern = f"kyc:unified:{user_id}_*"
        cache_keys = self.redis.keys(cache_key_pattern)
        if not cache_keys:
            logger.error(f"No active unified KYC session found for user_id: {user_id}")
            raise HTTPException(status_code=400, detail="No active unified KYC session found")

        # Use the most recent cache key (assuming only one active session per user)
        cache_key = cache_keys[0]
        cached_data = self.redis.get(cache_key)
        if not cached_data:
            logger.error(f"No active unified KYC session found for user_id: {user_id}")
            raise HTTPException(status_code=400, detail="No active unified KYC session found")

        cached_data = json.loads(cached_data)
        unified_transaction_id = cached_data.get("unified_transaction_id")
        if not unified_transaction_id:
            logger.error(f"No unified_transaction_id found in cache for user_id: {user_id}")
            raise HTTPException(status_code=400, detail="No unified transaction ID found")

        url = f"{self.uat_base_url}/kyc-unified/v1/{unified_transaction_id}/details/"
        headers = self.get_auth_header_basic()

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers)

        if response.status_code != 200:
            logger.error(f"Failed to retrieve KYC details: {response.status_code} {response.text}")
            raise HTTPException(status_code=response.status_code, detail=response.text)

        data = response.json()
        logger.info(f"Unified KYC data: {data}")

        if data.get("code") != "200":
            error_msg = data.get("msg", "Failed to retrieve KYC details")
            logger.error(f"Failed to retrieve KYC details: {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)

        model = data.get("model")

        # Fetch user from database
        uuid_obj = UUID(user_id)
        user = await session.get(User, uuid_obj)
        if not user:
            logger.error(f"User not found: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")

        # Update user with Aadhaar details
        user.aadhaar_number = model.get("maskedAdharNumber")
        address = model.get("address", {})
        user.address = ", ".join(filter(None, [
            address.get("house", ""),
            address.get("street", ""),  # Use 'street' as per response
            address.get("landmark", ""),
            address.get("loc", ""),
            address.get("po", ""),
            address.get("dist", ""),
            address.get("subdist", ""),
            address.get("vtc", ""),
            address.get("pc", ""),
            address.get("state", ""),
            address.get("country", "")
        ]))
        user.country = address.get("country")
        user.state = address.get("state")
        user.gender = model.get("gender")
        user.date_of_birth = model.get("dob")
        care_of = model.get("careOf")
        user.care_of = care_of

        # Extract parent name from care_of
        match = re.match(r"(S/O|D/O|C/O)\s+(.*)", care_of or "", re.IGNORECASE)
        father_name = match.group(2) if match else None
        user.father_name = father_name or care_of

        # Split name for first_name, middle_name, and last_name
        name_parts = model.get("name", "").split()
        if len(name_parts) >= 1:
            user.first_name = " ".join(name_parts[:-1])  # All but last part
            user.last_name = name_parts[-1]
            user.full_name = model.get("name")

        # Update or create KYC record
        statement = select(KYC).where(KYC.user_id == user_id)
        result = await session.execute(statement)
        kyc = result.scalar_one_or_none()
        if kyc:
            kyc.aadhaar_number = model.get("maskedAdharNumber", "").replace("x", "")
            kyc.updated_at = datetime.now()
            session.add(kyc)
        else:
            kyc = KYC(
                user_id=user_id,
                aadhaar_number=model.get("maskedAdharNumber", "").replace("x", ""),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            session.add(kyc)

        await session.merge(user)
        await session.commit()
        await session.refresh(user)
        await session.refresh(kyc)

        # Clear cache after successful submission
        self.redis.delete(cache_key)
        logger.info(f"Cleared cache for user_id: {user_id}, cache_key: {cache_key}")

        response_data = {
            "user_id": user_id, 
            "success": True, 
            "message": "Unified KYC details retrieved successfully"
        }
        return response_data