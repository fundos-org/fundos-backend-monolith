from typing import Dict, Optional
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.user import User, KycStatus
from src.models.kyc import KYC
from datetime import datetime, timezone
from uuid import UUID
import httpx
import json
import base64
import redis
import os
from src.logging.logging_setup import get_logger

logger = get_logger(__name__)

DIGITAP_BASE_URL = "https://svc.digitap.ai"
CLIENT_ID = "17137231"
CLIENT_SECRET = "RhoLU35zsKc2OMao9SNec3kpcHJjIWAk"
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = 6379
REDIS_DB = 0
CACHE_TTL = 300

class BankService:
    def __init__(self):
        self.base_url = DIGITAP_BASE_URL
        self.client_id = CLIENT_ID
        self.client_secret = CLIENT_SECRET
        self.redis = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True
        )

    def get_auth_header(self):
        """Generate header-based authentication header."""
        token = f"{self.client_id}:{self.client_secret}"
        base64_token = base64.b64encode(token.encode()).decode()
        return {
            "Authorization": f"Basic {base64_token}",
            "Content-Type": "application/json"
        }

    def _get_bank_cache_key(
        self, 
        user_id: str | UUID
    ) -> str:
        """Generate Redis cache key for bank verification."""
        return f"bank:verify:{str(user_id)}"

    async def initiate_verification(
        self, 
        user_id: UUID, 
        bank_details: Dict, 
        session: AsyncSession
    ) -> Dict:
        """
        Initiate bank account verification using Digitap Bank Data UI API.
        
        Args:
            user_id (UUID): UUID of the user.
            bank_details (Dict): Dictionary with bank_account_number, bank_ifsc, account_holder_name.
            session (AsyncSession): SQLAlchemy async session.
        
        Returns:
            Dict: Response with verification URL, request_id, and expiration.
        
        Raises:
            HTTPException: If validation or API call fails.
        """
        # Validate required bank details
        required_fields = ["bank_account_number", "bank_ifsc"]
        for field in required_fields:
            if not bank_details.get(field):
                logger.error(f"Missing required field: {field}")
                raise HTTPException(status_code=400, detail=f"{field} is required")

        # Fetch user
        user = await session.get(User, user_id)
        if not user:
            logger.error(f"User not found: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")

        # Check if bank verification is already completed
        kyc = await session.get(KYC, user_id)
        if kyc and kyc.status == KycStatus.VERIFIED and kyc.bank_account_number:
            logger.warning(f"Bank details already verified for user_id: {user_id}")
            raise HTTPException(status_code=400, detail="Bank details already verified")

        # Prepare payload for Generate URL API
        client_ref_num = f"bank-{user_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        payload = {
            "client_ref_num": client_ref_num,
            "txn_completed_cburl": "https://your-app.com/api/bank/callback",
            "destination": "netbanking",
            "return_url": "https://your-app.com/return?request_id=%s&txn_id=%s&status=%s",
            "start_month": datetime.now().strftime("%Y-%m"),
            "end_month": datetime.now().strftime("%Y-%m"),
            "acceptance_policy": "atLeastOneTransactionInRange",
            "relaxation_days": 0
        }

        # Prepare headers
        headers = self.get_auth_header()

        # Call Generate URL API
        url = f"{self.base_url}/bank-data/generateurl"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)

        if response.status_code != 200:
            logger.error(f"Failed to generate URL: {response.status_code} {response.text}")
            raise HTTPException(status_code=response.status_code, detail="Failed to initiate verification")

        data = response.json()
        if data.get("status") != "success":
            logger.error(f"Generate URL error: {data.get('code')} - {data.get('msg')}")
            raise HTTPException(status_code=400, detail=f"Generate URL failed: {data.get('msg')}")

        # Store in Redis
        cache_key = self._get_bank_cache_key(user_id)
        cache_data = {
            "request_id": data["request_id"],
            "url": data["url"],
            "expires": data["expires"],
            "client_ref_num": client_ref_num,
            "bank_account_number": bank_details["bank_account_number"],
            "bank_ifsc": bank_details["bank_ifsc"],
            "account_holder_name": bank_details.get("account_holder_name")
        }
        self.redis.setex(cache_key, CACHE_TTL, json.dumps(cache_data))
        logger.info(f"Cached data for user_id: {user_id}")

        # Update KYC
        if not kyc:
            kyc = KYC(
                user_id=user_id,
                status=KycStatus.PENDING,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            session.add(kyc)
        kyc.bank_account_number = bank_details["bank_account_number"]
        kyc.bank_ifsc = bank_details["bank_ifsc"]
        kyc.status = KycStatus.PENDING
        kyc.updated_at = datetime.now()

        # Update User
        user.updated_at = datetime.now()
        if bank_details.get("account_holder_name"):
            user.first_name = user.first_name or bank_details["account_holder_name"].split()[0]
            user.last_name = user.last_name or " ".join(bank_details["account_holder_name"].split()[1:]) if len(bank_details["account_holder_name"].split()) > 1 else None

        await session.merge(kyc)
        await session.merge(user)
        await session.commit()
        await session.refresh(kyc)
        await session.refresh(user)

        return {
            "status": "success",
            "message": "Verification initiated. Complete using the URL.",
            "url": data["url"],
            "request_id": data["request_id"],
            "expires": data["expires"]
        }

    async def handle_callback(
        self, 
        data: Dict, 
        session: AsyncSession
    ):
        """
        Handle Digitap transaction completion callback.
        
        Args:
            data (Dict): Callback data from Digitap.
            session (AsyncSession): SQLAlchemy async session.
        
        Returns:
            Dict: Acknowledgment of callback.
        
        Raises:
            HTTPException: If callback processing fails.
        """
        logger.info(f"Received callback: {data}")

        # Validate callback header
        callback_type = data.get("headers", {}).get("x-digitap-callback-type")
        if callback_type != "TRANSACTION_COMPLETE":
            logger.error(f"Invalid callback type: {callback_type}")
            raise HTTPException(status_code=400, detail="Invalid callback type")

        # Extract data
        txn_id = data.get("txn_id")
        status = data.get("status")
        code = data.get("code")
        client_ref_num = data.get("client_ref_num")
        request_id = data.get("request_id")

        if not all([txn_id, status, client_ref_num, request_id]):
            logger.error(f"Missing callback fields: {data}")
            raise HTTPException(status_code=400, detail="Missing required fields")

        # Extract user_id
        try:
            user_id = client_ref_num.split("-")[1]
            UUID(user_id)
        except (IndexError, ValueError):
            logger.error(f"Invalid client_ref_num: {client_ref_num}")
            raise HTTPException(status_code=400, detail="Invalid client_ref_num")

        # Fetch user and KYC
        user = await session.get(User, UUID(user_id))
        if not user:
            logger.error(f"User not found: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")
        kyc = await session.get(KYC, user_id)
        if not kyc:
            logger.error(f"KYC not found: {user_id}")
            raise HTTPException(status_code=404, detail="KYC not found")

        # Update based on status
        if status == "Success" and code == "ReportGenerated":
            kyc.status = KycStatus.PENDING
            logger.info(f"Transaction success for user_id: {user_id}, txn_id: {txn_id}")
        else:
            kyc.status = KycStatus.REJECTED
            logger.warning(f"Transaction failed for user_id: {user_id}, code: {code}")

        kyc.updated_at = datetime.now()
        user.updated_at = datetime.now()
        await session.merge(kyc)
        await session.merge(user)
        await session.commit()

        # Clear Redis cache
        self.redis.delete(self._get_bank_cache_key(user_id))
        logger.info(f"Cleared cache for user_id: {user_id}")

        return {"status": "received"}

    async def check_status(
        self, 
        user_id: UUID, 
        request_id: str, 
        session: AsyncSession
    ) -> Dict:
        """
        Check bank verification status using Digitap Status Check API.
        
        Args:
            user_id (UUID): UUID of the user.
            request_id (str): Request ID from initiate_verification.
            session (AsyncSession): SQLAlchemy async session.
        
        Returns:
            Dict: Status check response.
        
        Raises:
            HTTPException: If status check fails.
        """
        headers = self.get_auth_header()
        payload = {"request_id": request_id}
        url = f"{self.base_url}/bank-data/statuscheck"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)

        if response.status_code != 200:
            logger.error(f"Status check failed: {response.status_code} {response.text}")
            raise HTTPException(status_code=response.status_code, detail="Status check failed")

        data = response.json()
        if data.get("status") != "success":
            logger.error(f"Status check error: {data.get('code')} - {data.get('msg')}")
            raise HTTPException(status_code=400, detail=f"Status check failed: {data.get('msg')}")

        logger.info(f"Status check for user_id: {user_id}, status: {data.get('txn_status')}")

        return {
            "status": "success",
            "txn_status": data.get("txn_status"),
            "txn_id": data.get("txn_id")
        }

    async def retrieve_report(
        self, 
        user_id: UUID, 
        txn_id: str, 
        session: AsyncSession
    ) -> Dict:
        """
        Retrieve bank verification report using Digitap Retrieve Report API.
        
        Args:
            user_id (UUID): UUID of the user.
            txn_id (str): Transaction ID from callback or status check.
            session (AsyncSession): SQLAlchemy async session.
        
        Returns:
            Dict: Verification report details.
        
        Raises:
            HTTPException: If report retrieval fails.
        """
        # Fetch KYC
        kyc = await session.get(KYC, user_id)
        if not kyc:
            logger.error(f"KYC not found: {user_id}")
            raise HTTPException(status_code=404, detail="KYC not found")

        headers = self.get_auth_header()
        payload = {
            "txn_id": txn_id,
            "report_type": "json",
            "report_subtype": "type1"
        }
        url = f"{self.base_url}/bank-data/retrievereport"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)

        if response.status_code != 200:
            logger.error(f"Report retrieval failed: {response.status_code} {response.text}")
            raise HTTPException(status_code=response.status_code, detail="Report retrieval failed")

        data = response.json()
        if data.get("status") != "success":
            logger.error(f"Report retrieval error: {data.get('code')} - {data.get('msg')}")
            raise HTTPException(status_code=400, detail=f"Report retrieval failed: {data.get('msg')}")

        # Update KYC
        report = data.get("report", {})
        kyc.status = KycStatus.VERIFIED
        kyc.updated_at = datetime.now()

        # Update User
        user = await session.get(User, user_id)
        if user:
            user.updated_at = datetime.now()
            if report.get("beneficiary_name"):
                user.first_name = user.first_name or report["beneficiary_name"].split()[0]
                user.last_name = user.last_name or " ".join(report["beneficiary_name"].split()[1:]) if len(report["beneficiary_name"].split()) > 1 else None

        await session.merge(kyc)
        await session.merge(user)
        await session.commit()
        await session.refresh(kyc)
        await session.refresh(user)

        logger.info(f"Report retrieved for user_id: {user_id}, txn_id: {txn_id}")

        return {
            "status": "success",
            "message": "Bank details verified",
            "beneficiary_name": report.get("beneficiary_name"),
            "is_name_match": report.get("is_name_match"),
            "matching_score": report.get("matching_score")
        }

    async def get_institution_id(
        self, 
        bank_name: str
    ) -> Optional[str]:
        """
        Fetch institution_id for a bank_name using Digitap Institution List API.
        
        Args:
            bank_name (str): Name of the bank.
        
        Returns:
            Optional[str]: institution_id if found, else None.
        
        Raises:
            HTTPException: If API call fails.
        """
        headers = self.get_auth_header()
        url = f"{self.base_url}/bank-data/institutions"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params={"type": "NetBanking"}, headers=headers)

        if response.status_code != 200:
            logger.error(f"Institution list failed: {response.status_code} {response.text}")
            raise HTTPException(status_code=response.status_code, detail="Failed to fetch institutions")

        data = response.json()
        if data.get("status") != "success":
            logger.error(f"Institution list error: {data.get('code')} - {data.get('msg')}")
            raise HTTPException(status_code=400, detail=f"Institution list failed: {data.get('msg')}")

        for inst in data.get("data", []):
            if inst["name"].lower() == bank_name.lower():
                logger.info(f"Found institution_id: {inst['id']} for bank: {bank_name}")
                return inst["id"]
        
        logger.warning(f"No institution_id found for bank: {bank_name}")
        return None