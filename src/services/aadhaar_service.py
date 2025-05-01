import httpx
import base64
from fastapi import HTTPException

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

    async def initiate_kyc(self, unique_id: str, aadhaar_number: str) -> dict:
        url = f"{self.base_url}/ent/v3/kyc/intiate-kyc-auto"
        payload = {
            "uniqueId": unique_id,
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

    async def submit_aadhaar_otp(self, otp: str, transaction_id: str, code_verifier: str, fwdp: str, share_code: str = "5678") -> dict:
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

        user_data = data.get("model", {})

        return user_data
    
    async def resend_aadhaar_otp(self, unique_id: str, aadhaar_number: str, transaction_id: str, fwdp: str) -> dict:
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

        model = data.get("model", {})

        return {
            "transaction_id": model.get("transactionId"),
            "fwdp": model.get("fwdp"),
            "code_verifier": model.get("codeVerifier"),
            "message": data.get("msg", "OTP resent successfully")
        }

    