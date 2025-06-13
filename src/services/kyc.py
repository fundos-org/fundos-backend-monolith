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
from src.models.kyc import KYC, KycStatus
from src.models.user import User, OnboardingStatus
from src.logging.logging_setup import get_logger
from datetime import datetime
from src.configs.configs import redis_configs
from src.configs.configs import digitap_configs

# Configure logging
logger = get_logger(__name__)

DIGITAP_BASE_URL = digitap_configs.digitap_base_url
VALIDATION_BASE_URL = digitap_configs.validation_base_url
CLIENT_ID = digitap_configs.client_id
CLIENT_SECRET = digitap_configs.client_secret
REDIS_HOST = redis_configs.redis_host
REDIS_PORT = redis_configs.redis_port
REDIS_DB = redis_configs.redis_db
CACHE_TTL = redis_configs.redis_cache_ttl  # 5 minutes in seconds, aligned with likely Digitap session timeout

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
    async def send_aadhaar_otp(
        self, 
        user_id: str, 
        aadhaar_number: str, 
        session: AsyncSession
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

    async def submit_aadhaar_otp(
        self, 
        user_id: str, 
        otp: str, 
        session: AsyncSession, 
        share_code: str = "1234"
    ) -> dict:
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
        user.country = address.get("country")
        user.state = address.get("state")
        user.gender = model.get("gender")
        user.date_of_birth = model.get("dob")
        care_of = model.get("careOf")
        user.care_of = care_of

        match = re.match(r"(S/O|D/O|C/O)\s+(.*)", care_of, re.IGNORECASE)
        father_name = match.group(2) if match else None
        user.father_name = father_name

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

        response_data = {
            "user_id": user_id, 
            "aadhaar_data": model, 
            "success": True
        }
        return response_data

    async def resend_aadhaar_otp(
        self, 
        user_id: str, 
        aadhaar_number: str, 
        session: AsyncSession
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
            logger.error(f"OTP resend rate limit exceeded for user_id: {user_id}")
            raise HTTPException(status_code=429, detail="Please wait 60 seconds before resending OTP")

        cache_key = self._get_cache_key(user_id)
        cached_data = self.redis.get(cache_key)
        if not cached_data:
            logger.error(f"No active Aadhaar OTP session found for user_id: {user_id}")
            raise HTTPException(status_code=400, detail="No active Aadhaar OTP session found")

        cached_data = json.loads(cached_data)
        transaction_id = cached_data["transaction_id"]
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
    async def verify_pan(
        self, 
        user_id: str, 
        pan_number: str, 
        session: AsyncSession
    ) -> dict:
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
        stmt = select(KYC).where(KYC.user_id == user_id)
        db_result = await session.execute(stmt)
        kyc = db_result.scalars().first()

        if kyc:
            # pull aadhaar num: 
            kyc_aadhaar_num = kyc.aadhaar_number
            kyc_masked_aadhaar = kyc_aadhaar_num[-4:] 

            if masked_aadhaar == kyc_masked_aadhaar: 
                kyc.pan_aadhaar_linked = True

            kyc.pan_number = result.get("pan")
            kyc.updated_at = datetime.now()
            await session.merge(kyc)
        else:
            result = {
                "user_id": user_id,
                "success": False,
                "message": "Verify Aadhaar first",
            }

        user.first_name = f"{result.get('first_name')} {result.get('middle_name')}"
        user.last_name = result.get("last_name")
        user.full_name = f"{user.first_name} {user.last_name}"
        
        await session.merge(user)
        await session.commit()
        await session.refresh(user)
        await session.refresh(kyc)

        response_data = {
            "user_id": user_id,
            "pan_data" : result, 
            "success": True
        }

        return response_data

    async def verify_pan_bank_link(
        self, 
        user_id: str, 
        pan_number: str, 
        bank_account_number: str, 
        ifsc_code: str, 
        session: AsyncSession
    ) -> dict:
        try:
            UUID(user_id)
        except ValueError:
            logger.error(f"Invalid user_id format: {user_id}")
            raise HTTPException(status_code=400, detail="Invalid user_id format")

        url = "https://svc.digitap.ai/validation/misc/v1/pan-account-linkage" # 
        demo_url = "https://svcdemo.digitap.work/validation/misc/v1/pan-account-linkage" # change it to a variable later
        payload = {
            "client_ref_num": f"pan-bank-{user_id}",
            "pan": pan_number,
            "account_number": bank_account_number,
            "ifsc_code": ifsc_code
        }
        headers = self.get_auth_header_basic()

        demo_headers = {
            "Content-Type": "application/json",
            "Authorization": "Basic NDcxMzU3Njk6QVhsODZIcW9HSjYwMXNWWWVIMGNEVEtUQUNuaklwdTE="
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(demo_url, json=payload, headers=demo_headers)

        if response.status_code != 200:
            logger.error(f"PAN to Bank Account link verification failed: {response.status_code} {response.text}")
            raise HTTPException(status_code=response.status_code, detail="Failed to verify PAN to Bank Account link")

        data = response.json()
        logger.info(f"PAN to Bank Account link verification response: {data}")

        if data.get("result_code") != 101:
            raise HTTPException(status_code=400, detail=data.get("message", "PAN to Bank Account link verification unsuccessful"))

        result = data.get("result", {})
        linked_status = result.get("linked_status", False) 

        if not linked_status: 
            raise HTTPException(status_code=400, detail="PAN to Bank Account link verification unsuccessful")

        # Fetch user from database
        uuid_obj = UUID(user_id)
        user = await session.get(User, uuid_obj)
        if not user:
            logger.error(f"User not found: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update or create KYC record
        stmt = select(KYC).where(KYC.user_id == user_id)
        db_result = await session.execute(stmt)
        kyc = db_result.scalars().first()

        if kyc:
            kyc.bank_account_number = bank_account_number
            kyc.bank_ifsc = ifsc_code
            kyc.pan_bank_linked = linked_status
            kyc.status = KycStatus.VERIFIED.name if linked_status else KycStatus.PENDING.name
            user.kyc_status = KycStatus.VERIFIED.name if linked_status else KycStatus.PENDING.name
            kyc.updated_at = datetime.now()
            await session.merge(kyc)
            await session.merge(user)
        else: 
            return {
                "message": "KYC record not found",
                "success": False,
            }

        await session.commit()
        await session.refresh(kyc)
        await session.refresh(user)

        response_data = {
            "user_id": user_id,
            "pan_bank_link_data" : result,
            "success": True
        }

        return response_data