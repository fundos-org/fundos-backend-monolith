import httpx
import base64
from fastapi import HTTPException

DIGITAP_BASE_URL = "https://svc.digitap.ai/validation"
CLIENT_ID = "17137231"
CLIENT_SECRET = "RhoLU35zsKc2OMao9SNec3kpcHJjIWAk"

class ValidationService:
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

    async def validate_pan_aadhaar_link(self, client_ref_num: str, pan_number: str, aadhaar_number: str) -> dict:
        url = f"{self.base_url}/kyc/v1/pan_aadhaar_link" 
        payload = {
            "client_ref_num": client_ref_num,
            "pan": pan_number,
            "aadhaar": aadhaar_number
        }
        headers = self.get_auth_header_basic()

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to validate PAN-Aadhaar link")

        data = response.json()

        if data.get("code") != "200":
            raise HTTPException(status_code=400, detail=data.get("msg", "PAN-Aadhaar link validation failed"))

        return {
            "linked": data.get("model", {}).get("linked"),
            "message": data.get("msg")
        }

    async def validate_pan(self, client_ref_num: str, pan_number: str, full_name: str, name_match_method: str = "dg_name_match") -> dict:
        url = f"{self.base_url}/kyc/v1/pan_basic"
        payload = {
            "client_ref_num": client_ref_num,
            "pan": pan_number,
            "name": full_name,
            "name_match_method": name_match_method
        }
        headers = self.get_auth_header_basic()

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to validate PAN")

        data = response.json()

        if data.get("code") != "200":
            raise HTTPException(status_code=400, detail=data.get("msg", "PAN validation failed"))

        return {
            "full_name": data.get("model", {}).get("fullName"),
            "pan_status": data.get("model", {}).get("status"),
            "message": data.get("msg")
        }

    async def validate_aadhaar(self, client_ref_num: str, aadhaar_number: str) -> dict:
        url = f"{self.base_url}kyc/v1/basic_aadhaar"
        payload = {
            "client_ref_num": client_ref_num,
            "aadhaar": aadhaar_number
        }
        headers = self.get_auth_header()

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to validate Aadhaar")

        data = response.json()

        if data.get("code") != "200":
            raise HTTPException(status_code=400, detail=data.get("msg", "Aadhaar validation failed"))

        return {
            "is_valid": data.get("model", {}).get("valid"),
            "message": data.get("msg")
        }
