import httpx
import base64
from fastapi import HTTPException

DIGITAP_BASE_URL = "https://svc.digitap.ai"
CLIENT_ID = "your_client_id"
CLIENT_SECRET = "your_client_secret"

class PANService:
    def __init__(self):
        self.base_url = DIGITAP_BASE_URL
        self.client_id = CLIENT_ID
        self.client_secret = CLIENT_SECRET

    def get_auth_header(self) -> dict:
        token = f"{self.client_id}:{self.client_secret}"
        base64_token = base64.b64encode(token.encode()).decode()
        return {
            "Authorization": f"Basic {base64_token}",
            "Content-Type": "application/json"
        }

    async def verify_pan(self, unique_id: str, pan_number: str) -> dict:
        url = f"{self.base_url}/validation/kyc/v1/pan_details"
        payload = {
            "client_ref_num": unique_id,
            "pan": pan_number
        }
        headers = self.get_auth_header()

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to verify PAN")

        data = response.json()

        if data.get("result_code") != 101:
            raise HTTPException(status_code=400, detail=data.get("message", "PAN verification failed"))

        return data.get("result", {})
