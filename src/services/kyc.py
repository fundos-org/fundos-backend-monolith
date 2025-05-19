import httpx
import base64
import redis
import json
import os
from fastapi import HTTPException
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.kyc import KYC, KycStatus
from src.models.user import User
from src.logging.logging_setup import get_logger
from datetime import datetime


# Configure logging
logger = get_logger(__name__)

DIGITAP_BASE_URL = "https://svc.digitap.ai"
VALIDATION_BASE_URL = "https://svc.digitap.ai/validation"
CLIENT_ID = "17137231"
CLIENT_SECRET = "RhoLU35zsKc2OMao9SNec3kpcHJjIWAk"
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = 6379
REDIS_DB = 0
CACHE_TTL = 300  # 5 minutes in seconds, aligned with likely Digitap session timeout

class KycService:
    def __init__(self):
        self.base_url = DIGITAP_BASE_URL
        self.validation_base_url = VALIDATION_BASE_URL
        self.client_id = CLIENT_ID
        self.client_secret = CLIENT_SECRET
        self.redis = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True
        )

    def get_auth_header(self) -> dict:
        token = f"{self.client_id}:{self.client_secret}"
        base64_token = base64.b64encode(token.encode()).decode()
        return {
            "Authorization": f"{base64_token}",
            "Content-Type": "application/json"
        }

    def get_auth_header_basic(self) -> dict:
        token = f"{self.client_id}:{self.client_secret}"
        base64_token = base64.b64encode(token.encode()).decode()
        return {
            "Authorization": f"Basic {base64_token}",
            "Content-Type": "application/json"
        }

    def _get_cache_key(self, user_id: str | UUID) -> str:
        return f"kyc:aadhaar:{str(user_id)}"

    def _get_rate_limit_key(self, user_id: str | UUID) -> str:
        return f"kyc:rate_limit:{str(user_id)}"

    # Aadhaar Methods
    async def send_aadhaar_otp(self, user_id: str, aadhaar_number: str, session: AsyncSession) -> dict:
        try:
            # Validate user_id as UUID
            UUID(user_id)
        except ValueError:
            logger.error(f"Invalid user_id format: {user_id}")
            raise HTTPException(status_code=400, detail="Invalid user_id format")

        # Check rate limit (60-second interval)
        rate_limit_key = self._get_rate_limit_key(user_id)
        if self.redis.get(rate_limit_key):
            logger.error(f"OTP request rate limit exceeded for user_id: {user_id}")
            raise HTTPException(status_code=429, detail="Please wait 60 seconds before requesting a new OTP")

        url = f"{self.base_url}/ent/v3/kyc/intiate-kyc-auto"
        payload = {
            "uniqueId": user_id,  # Send as string to Digitap
            "uid": aadhaar_number
        }
        headers = self.get_auth_header()

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)

        if response.status_code != 200:
            logger.error(f"Failed to initiate Aadhaar KYC: {response.status_code} {response.text}")
            raise HTTPException(status_code=response.status_code, detail="Failed to initiate Aadhaar KYC")

        data = response.json()
        response_data = {
            "transaction_id": data["model"]["transactionId"],
            "fwdp": data["model"]["fwdp"],
            "code_verifier": data["model"]["codeVerifier"],
            "aadhaar_number": aadhaar_number
        }

        # Store in Redis
        cache_key = self._get_cache_key(user_id)
        self.redis.setex(cache_key, CACHE_TTL, json.dumps(response_data))
        # Set rate limit key (60 seconds)
        self.redis.setex(rate_limit_key, 60, "1")
        logger.info(f"Cached OTP data for user_id: {user_id}, cache_key: {cache_key}")

        return response_data

    async def submit_aadhaar_otp(self, user_id: str, otp: str, session: AsyncSession, share_code: str = "1234") -> dict:
        # Convert UUID to string for Redis
        cache_key = self._get_cache_key(user_id)
        cached_data = self.redis.get(cache_key)
        if not cached_data:
            logger.error(f"No active Aadhaar OTP session found for user_id: {user_id}")
            raise HTTPException(status_code=400, detail="No active Aadhaar OTP session found")

        cached_data = json.loads(cached_data)
        transaction_id = cached_data["transaction_id"]
        fwdp = cached_data["fwdp"]
        code_verifier = cached_data["code_verifier"]

        url = f"{self.base_url}/ent/v3/kyc/submit-otp"
        payload = {
            "shareCode": share_code,
            "otp": otp,
            "transactionId": transaction_id,
            "codeVerifier": code_verifier,
            "fwdp": fwdp,
            "validateXml": True
        }
        headers = self.get_auth_header()

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)

        if response.status_code != 200:
            logger.error(f"Failed to submit OTP: {response.status_code} {response.text}")
            raise HTTPException(status_code=response.status_code, detail="Failed to submit OTP")

        data = response.json()
        logger.info(f"Digitap API response: {data}")

        if data.get("code") != "200":
            error_msg = data.get("msg", "OTP submission failed")
            error_code = data.get("errorCode", "")
            logger.error(f"OTP submission failed: {error_msg}, error_code: {error_code}")
            if error_msg == "this is no longer active" or error_code == "E0013":  # E0013: OTP expired
                # Clear invalid cache
                self.redis.delete(cache_key)
                logger.info(f"Cleared invalid cache for user_id: {user_id}")
                raise HTTPException(
                    status_code=400,
                    detail="OTP session has expired. Please request a new OTP using /aadhaar/otp/send."
                )
            if error_code == "E0010":  # Incorrect OTP
                raise HTTPException(
                    status_code=400,
                    detail="Incorrect OTP. Please try again or request a new OTP using /aadhaar/otp/send."
                )
            raise HTTPException(status_code=400, detail=error_msg)

        model: dict = data.get("model")

        # Fetch user from database
        uuid_obj = UUID(user_id)
        user = await session.get(User, uuid_obj)
        if not user:
            logger.error(f"User not found: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")

        # Update user with Aadhaar details
        user.aadhaar_number = model.get("adharNumber")
        address = model.get("address", {})
        user.address = ", ".join(filter(None, [
            address.get("house", ""),
            address.get("street", ""),
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
        user.gender = model.get("gender")
        user.date_of_birth = model.get("dob")
        user.care_of = model.get("careOf")

        # Update or create KYC record
        kyc = await session.get(KYC, user_id)
        if kyc:
            kyc.aadhaar_number = model.get("adharNumber")
            kyc.updated_at = datetime.now()
            session.add(kyc)
        else:
            kyc = KYC(
                user_id=user_id,
                aadhaar_number=model.get("adharNumber"),
                status="pending",
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
        logger.info(f"Cleared cache for user_id: {user_id}")

        return model

    async def resend_aadhaar_otp(self, user_id: str, aadhaar_number: str, session: AsyncSession) -> dict:
        try:
            # Validate user_id as UUID
            UUID(user_id)
        except ValueError:
            logger.error(f"Invalid user_id format: {user_id}")
            raise HTTPException(status_code=400, detail="Invalid user_id format")

        # Check rate limit (60-second interval)
        rate_limit_key = self._get_rate_limit_key(user_id)
        if self.redis.get(rate_limit_key):
            logger.error(f"OTP resend rate limit exceeded for user_id: {user_id}")
            raise HTTPException(status_code=429, detail="Please wait 60 seconds before resending OTP")

        cache_key = self._get_cache_key(user_id)
        cached_data = self.redis.get(cache_key)
        if not cached_data:
            logger.error(f"No active Aadhaar OTP session found for user_id: {user_id}")
            raise HTTPException(status_code=400, detail="No active Aadhaar OTP session found")

        cached_data = json.loads(cached_data)
        transaction_id = cached_data["transaction_id"]
        fwdp = cached_data["fwdp"]

        url = f"{self.base_url}/ent/v3/kyc/resend-otp"
        payload = {
            "uniqueId": user_id,
            "uid": aadhaar_number,
            "transactionId": transaction_id,
            "fwdp": fwdp
        }
        headers = self.get_auth_header()

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)

        if response.status_code != 200:
            logger.error(f"Failed to resend OTP: {response.status_code} {response.text}")
            raise HTTPException(status_code=response.status_code, detail="Failed to resend Aadhaar OTP")

        data = response.json()

        if data.get("code") != "200":
            error_msg = data.get("msg", "Resend OTP failed")
            error_code = data.get("errorCode", "")
            logger.error(f"Resend OTP failed: {error_msg}, error_code: {error_code}")
            if error_msg == "this is no longer active" or error_code == "E0013":  # E0013: OTP expired
                # Clear invalid cache
                self.redis.delete(cache_key)
                logger.info(f"Cleared invalid cache for user_id: {user_id}")
                raise HTTPException(
                    status_code=400,
                    detail="OTP session has expired. Please request a new OTP using /aadhaar/otp/send."
                )
            raise HTTPException(status_code=400, detail=error_msg)

        model: dict = data.get("model", {})
        response_data = {
            "transaction_id": model.get("transactionId"),
            "fwdp": model.get("fwdp"),
            "code_verifier": model.get("codeVerifier"),
            "aadhaar_number": aadhaar_number,
            "message": data.get("msg", "OTP resent successfully")
        }

        # Update cache with new data
        self.redis.setex(cache_key, CACHE_TTL, json.dumps(response_data))
        # Set rate limit key (60 seconds)
        self.redis.setex(rate_limit_key, 60, "1")
        logger.info(f"Updated cache for user_id: {user_id}")

        return response_data

    # PAN Methods
    async def verify_pan(self, user_id: str, pan_number: str, session: AsyncSession) -> dict:
        try:
            UUID(user_id)
        except ValueError:
            logger.error(f"Invalid user_id format: {user_id}")
            raise HTTPException(status_code=400, detail="Invalid user_id format")

        url = f"{self.validation_base_url}/kyc/v1/pan_details"
        payload = {
            "client_ref_num": "pan-" + user_id,
            "pan": pan_number
        }
        headers = self.get_auth_header_basic()

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)

        if response.status_code != 200:
            logger.error(f"PAN verification failed: {response.status_code} {response.text}")
            raise HTTPException(status_code=response.status_code, detail="PAN verification failed")

        data = response.json()
        logger.info(f"PAN verification response: {data}")

        if data.get("result_code") != 101:
            raise HTTPException(status_code=400, detail="PAN verification unsuccessful")

        result = data.get("result", {})

        pan_status = result.get("pan_status")
        aadhaar_linked = result.get("aadhaar_linked")
        aadhaar_num = result.get("aadhaar_number") 

        if pan_status:
            logger.info(f"pan status: {pan_status}")

        else: 
            logger.error(f"pan status: {pan_status}") 
            
        if aadhaar_linked and aadhaar_num: 
            masked_aadhaar = aadhaar_num[-4:]
        else: 
            logger.error("aadhaar number unavailable unable to check pan aadhaar link")

        # Fetch and update user
        uuid_obj = UUID(user_id)
        user = await session.get(User, uuid_obj)
        if not user:
            logger.error(f"User not found: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")

        # Update or create KYC record
        kyc = await session.get(KYC, user_id)
        if kyc:
            # pull aadhaar num: 
            kyc_aadhaar_num = kyc.aadhaar_number
            kyc_masked_aadhaar = kyc_aadhaar_num[-4:] 

            if masked_aadhaar == kyc_masked_aadhaar: 
                kyc.pan_aadhaar_linked = True

            kyc.pan_number = result.get("pan")
            kyc.status = KycStatus.VERIFIED
            kyc.updated_at = datetime.now()
            await session.merge(kyc)
        else:
            kyc = KYC(
                user_id=user_id,
                pan_number=result.get("pan"),
                status="pending",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            session.add(kyc)

        await session.merge(user)
        await session.commit()
        await session.refresh(user)
        await session.refresh(kyc)

        return result

    