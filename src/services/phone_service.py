import httpx
import base64
from fastapi import HTTPException

PLIVO_AUTH_ID = "your_auth_id"
PLIVO_AUTH_TOKEN = "your_auth_token"
PLIVO_BASE_URL = f"https://api.plivo.com/v1/Account/{PLIVO_AUTH_ID}"

class PhoneService:
    def __init__(self):
        self.auth_id = PLIVO_AUTH_ID
        self.auth_token = PLIVO_AUTH_TOKEN
        self.base_url = PLIVO_BASE_URL

    def get_auth_header(self) -> dict:
        token = f"{self.auth_id}:{self.auth_token}"
        base64_token = base64.b64encode(token.encode()).decode()
        return {
            "Authorization": f"Basic {base64_token}",
            "Content-Type": "application/json"
        }

    async def verify_phone_number(self, phone_number: str, alias: str = "UserVerification", channel: str = "sms") -> dict:
        url = f"{self.base_url}/VerifiedCallerId/"
        payload = {
            "phone_number": phone_number,
            "alias": alias,
            "channel": channel
        }
        headers = self.get_auth_header()

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)

        if response.status_code != 201:
            raise HTTPException(status_code=response.status_code, detail="Failed to initiate phone number verification")

        data = response.json()
        return {
            "message": data.get("message"),
            "verification_uuid": data.get("verification_uuid")
        }
    async def verify_otp(self, session_uuid: str, otp_code: str) -> dict:
        url = f"{self.base_url}/Verify/Session/{session_uuid}/"
        payload = {
            "otp": otp_code
        }
        headers = self.get_auth_header()

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to verify OTP")

        data = response.json()

        if not data.get("verified"):
            raise HTTPException(status_code=400, detail="Invalid OTP")

        return data
