import httpx
import base64
from fastapi import HTTPException
from uuid import UUID 
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.kyc import KYC
from src.models.user import KycStatus, User
from datetime import datetime, timezone

DIGITAP_BASE_URL = "https://svc.digitap.ai"
CLIENT_ID = "17137231"
CLIENT_SECRET = "RhoLU35zsKc2OMao9SNec3kpcHJjIWAk"

class AadhaarService:
    def __init__(self):
        self.base_url = DIGITAP_BASE_URL
        self.client_id = CLIENT_ID
        self.client_secret = CLIENT_SECRET

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

    async def send_aadhaar_otp(self, user_id: str, aadhaar_number: str, session: AsyncSession) -> dict:
        url = f"{self.base_url}/ent/v3/kyc/intiate-kyc-auto"
        payload = {
            "uniqueId": user_id,
            "uid": aadhaar_number
        }
        headers = self.get_auth_header()

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to initiate Aadhaar KYC")

        data = response.json()
        
        return {
            "transaction_id": data["model"]["transactionId"],
            "fwdp": data["model"]["fwdp"],
            "code_verifier": data["model"]["codeVerifier"]
        }

    async def submit_aadhaar_otp(self, user_id: UUID, otp: str, transaction_id: str, code_verifier: str, fwdp: str, session: AsyncSession, share_code: str = "5678") -> dict:
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
            raise HTTPException(status_code=response.status_code, detail="Failed to submit OTP")

        data = response.json()

        if data.get("code") != "200":
            raise HTTPException(status_code=400, detail=data.get("msg", "OTP submission failed"))

        model: dict = data.get("model")

        # Fetch user from database
        user = await session.get(User, user_id)
        if not user:
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
            kyc.updated_at = datetime.now(timezone.utc)
        else:
            kyc = KYC(
                user_id=user_id,
                aadhaar_number=model.get("adharNumber"),
                status=KycStatus.PENDING,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

        await session.merge(user)
        await session.merge(kyc)
        await session.commit()
        await session.refresh(user)
        await session.refresh(kyc)

        return model
    
    async def resend_aadhaar_otp(self, unique_id: str, aadhaar_number: str, transaction_id: str, fwdp: str, session: AsyncSession) -> dict:
        url = f"{self.base_url}/ent/v3/kyc/resend-otp"
        payload = {
            "uniqueId": unique_id,
            "uid": aadhaar_number,
            "transactionId": transaction_id,
            "fwdp": fwdp
        }
        headers = self.get_auth_header()

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to resend Aadhaar OTP")

        data = response.json()

        if data.get("code") != "200":
            raise HTTPException(status_code=400, detail=data.get("msg", "Resend OTP failed"))

        model: dict = data.get("model", {}) 
        
        return {
            "transaction_id": model.get("transactionId"),
            "fwdp": model.get("fwdp"),
            "code_verifier": model.get("codeVerifier"),
            "message": data.get("msg", "OTP resent successfully")
        }