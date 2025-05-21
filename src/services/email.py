import random
import string
import httpx
import redis
import os
from fastapi import HTTPException
from typing import Dict, Any
from src.logging.logging_setup import get_logger
from src.configs.configs import mail_configs

logger = get_logger(__name__)

# Zoho ZeptoMail configuration
ZEPTOMAIL_API_KEY = mail_configs.zeptomail_api_key
FROM_EMAIL = mail_configs.from_email
ZEPTOMAIL_URL = mail_configs.zeptomail_url

# Redis configuration
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = 6379
REDIS_DB = 0
CACHE_TTL = 300  # 5 minutes in seconds, aligned with KycService

class EmailService:
    def __init__(self):
        self.api_key = ZEPTOMAIL_API_KEY
        self.redis = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True
        )

    def _generate_otp(self, length: int = 6) -> str:
        """Generate a random OTP of specified length."""
        return ''.join(random.choices(string.digits, k=length))

    def _get_cache_key(self, email: str) -> str:
        """Generate Redis key for OTP storage."""
        return f"email:otp:{email}"

    def _get_rate_limit_key(self, email: str) -> str:
        """Generate Redis key for rate limiting."""
        return f"email:rate_limit:{email}"

    def get_auth_header(self) -> dict:
        """Return headers for Zoho ZeptoMail API authentication."""
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": self.api_key
        }

    async def send_email_otp(
        self, 
        email: str, 
        subject: str = "Your Verification Code"
    ) -> Any:
        """Send an OTP email using Zoho ZeptoMail."""
        try:
            # Check rate limit (60-second interval)
            rate_limit_key = self._get_rate_limit_key(email)
            if self.redis.get(rate_limit_key):
                logger.error(f"OTP request rate limit exceeded for email: {email}")
                raise HTTPException(status_code=429, detail="Please wait 60 seconds before requesting a new OTP")

            otp_code = self._generate_otp()
            cache_key = self._get_cache_key(email)
            
            # Store OTP in Redis with TTL
            try:
                self.redis.setex(cache_key, CACHE_TTL, otp_code)
                logger.info(f"Cached OTP for email: {email}, cache_key: {cache_key}")
            except redis.RedisError as e:
                logger.error(f"Redis error while storing OTP: {str(e)}")
                raise HTTPException(status_code=500, detail="Failed to store OTP in cache")

            body = f"Your OTP code is: {otp_code}"
            payload = {
                "from": {"address": FROM_EMAIL, "name": "FundOS"},
                "to": [{"email_address": {"address": email, "name": ""}}],
                "subject": subject,
                "htmlbody": f"<div><b>{body}</b></div>"
            }

            headers = self.get_auth_header()

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(ZEPTOMAIL_URL, json=payload, headers=headers)

            if response.status_code >= 400:
                logger.error(f"ZeptoMail API error: {response.text}")
                raise HTTPException(status_code=response.status_code, detail="Failed to send OTP email")

            # Set rate limit key (60 seconds)
            try:
                self.redis.setex(rate_limit_key, 60, "1")
            except redis.RedisError as e:
                logger.error(f"Redis error while setting rate limit: {str(e)}")
                raise HTTPException(status_code=500, detail="Failed to set rate limit")

            return {"message": "OTP sent successfully"}
        except redis.RedisError as e:
            logger.error(f"Redis error: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal error with cache service")
        except Exception as e:
            logger.error(f"Failed to send OTP email: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal error while sending OTP email")

    async def verify_email_otp(
        self, 
        email: str, 
        otp_code: str
    ) -> Any:
        """Verify the OTP for the given email."""
        try:
            cache_key = self._get_cache_key(email)
            valid_otp = self.redis.get(cache_key)

            if not valid_otp:
                logger.error(f"No OTP session found for email: {email}")
                raise HTTPException(status_code=404, detail="No OTP session found for this email")

            if otp_code != valid_otp:
                logger.error(f"Invalid OTP for email: {email}")
                raise HTTPException(status_code=400, detail="Invalid OTP")

            # Remove the OTP after successful verification
            try:
                self.redis.delete(cache_key)
                logger.info(f"Cleared OTP cache for email: {email}")
            except redis.RedisError as e:
                logger.error(f"Redis error while deleting OTP: {str(e)}")
                raise HTTPException(status_code=500, detail="Failed to clear OTP cache")

            return {"message": "Email verified successfully"}
        except redis.RedisError as e:
            logger.error(f"Redis error: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal error with cache service")
        except HTTPException as he:
            raise he
        except Exception as e:
            logger.error(f"Failed to verify OTP: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal error while verifying OTP")

    async def send_invitation_email(
        self,
        email: str,
        invite_code: str,
        subadmin_name: str = "",
        user_name: str = "",
        apk_link: str = "https://example.com/invite"
    ) -> Dict[str, str]:
        """Send an invitation email using Zoho ZeptoMail."""
        try:
            invite_link = f"{apk_link}?invite_code={invite_code}&email={email}"
            subject = "You have been invited to join a subadmin team"
            body_html = f"""
                <div>
                    <p>Hi {user_name or 'User'},</p>
                    <p>You have been invited by {subadmin_name or 'the team'} to join their subadmin team.</p>
                    <p>Please click on the following link to accept the invitation: <a href="{invite_link}">{invite_link}</a></p>
                    <p>Thank you,</p>
                    <p>Best regards,<br>{subadmin_name or 'The Team'}</p>
                </div>
            """

            payload = {
                "from": {"address": FROM_EMAIL, "name": "FundOS"},
                "to": [{"email_address": {"address": email, "name": user_name or ""}}],
                "subject": subject,
                "htmlbody": body_html
            }

            headers = self.get_auth_header()

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(ZEPTOMAIL_URL, json=payload, headers=headers)

            if response.status_code >= 400:
                logger.error(f"ZeptoMail API error: {response.text}")
                raise HTTPException(status_code=response.status_code, detail="Failed to send invitation email")

            return {
                "message": "Invitation sent successfully", 
                "success": True
            }

        except Exception as e:
            logger.error(f"Failed to send invitation email: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to send invitation email")