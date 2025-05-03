import random
import string
import httpx
from fastapi import HTTPException
from typing import Dict

SENDGRID_API_KEY = "your_sendgrid_api_key"
FROM_EMAIL = "your_verified_sender@example.com"
SENDGRID_URL = "https://api.sendgrid.com/v3/mail/send"

class EmailService:
    def __init__(self):
        self.api_key = SENDGRID_API_KEY

        # Simulated in-memory OTP storage (in production, use Redis or a DB)
        self.otp_sessions: Dict[str, str] = {}

    def _generate_otp(self, length: int = 6) -> str:
        return ''.join(random.choices(string.digits, k=length))

    def get_auth_header(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def send_email_otp(self, email: str, subject: str = "Your Verification Code") -> dict:
        otp_code = self._generate_otp()
        self.otp_sessions[email] = otp_code  # Store OTP against email

        body = f"Your OTP code is: {otp_code}"
        payload = {
            "personalizations": [{"to": [{"email": email}]}],
            "from": {"email": FROM_EMAIL},
            "subject": subject,
            "content": [{"type": "text/plain", "value": body}]
        }

        headers = self.get_auth_header()

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(SENDGRID_URL, json=payload, headers=headers)

        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail="Failed to send email")

        return {"message": "OTP sent successfully"}

    async def verify_email_otp(self, email: str, otp_code: str) -> dict:
        valid_otp = self.otp_sessions.get(email)

        if not valid_otp:
            raise HTTPException(status_code=404, detail="No OTP session found for this email")

        if otp_code != valid_otp:
            raise HTTPException(status_code=400, detail="Invalid OTP")

        # Optionally remove the OTP after successful verification
        del self.otp_sessions[email]

        return {"message": "Email verified successfully"}
