import random
import string
import smtplib
from email.message import EmailMessage
from pydantic import EmailStr
import redis
from fastapi import HTTPException
from typing import Dict, Any
from src.logging.logging_setup import get_logger
from src.configs.configs import mail_configs
from src.configs.configs import redis_configs

logger = get_logger(__name__)

# Zoho ZeptoMail SMTP configuration
SMTP_SERVER = mail_configs.smtp_server
SMTP_PORT = mail_configs.smtp_port_tls
SMTP_USERNAME = mail_configs.smtp_username
SMTP_PASSWORD = mail_configs.smtp_password  # Strip whitespace
FROM_EMAIL = mail_configs.from_email

# Redis configuration
REDIS_HOST = redis_configs.redis_host
REDIS_PORT = redis_configs.redis_port
REDIS_DB = redis_configs.redis_db
CACHE_TTL = redis_configs.redis_cache_ttl  # 5 minutes in seconds, aligned with KycService

class EmailService:
    def __init__(self):
        self.smtp_server = SMTP_SERVER
        self.smtp_port = SMTP_PORT
        self.smtp_username = SMTP_USERNAME
        self.smtp_password = SMTP_PASSWORD
        
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

    async def send_email_otp(
        self, 
        email: str, 
        subject: str = "FundOS Verification Code"
    ) -> Any:
        """Send an OTP email using Zoho ZeptoMail SMTP."""
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

            # Prepare email
            body = f"Hi, Welcome to Fundos. \n Your OTP code is: {otp_code}"
            msg = EmailMessage()
            msg['Subject'] = subject
            msg['From'] = f"fundos <{FROM_EMAIL}>"
            msg['To'] = email
            msg.set_content(body)  # Plain text
            msg.add_alternative(f"<div><b>{body}</b></div>", subtype='html')  # HTML content

            # Send email via SMTP
            try:
                with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=30.0) as server:
                    server.starttls()
                    server.login(self.smtp_username, self.smtp_password)
                    server.send_message(msg)
                logger.info(f"OTP email sent successfully to {email}")
            except smtplib.SMTPException as e:
                logger.error(f"SMTP error while sending OTP email: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Failed to send OTP email: {str(e)}")

            # Set rate limit key (60 seconds)
            try:
                self.redis.setex(rate_limit_key, 60, "1")
            except redis.RedisError as e:
                logger.error(f"Redis error while setting rate limit: {str(e)}")
                raise HTTPException(status_code=500, detail="Failed to set rate limit")

            return {"message": "OTP sent successfully", "success": True}
        except redis.RedisError as e:
            logger.error(f"Redis error: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal error with cache service")
        except Exception as e:
            logger.error(f"Failed to send OTP email: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Internal error while sending OTP email: {str(e)}")

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

            return {"message": "Email verified successfully", "success": True}
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
        """Send an invitation email using Zoho ZeptoMail SMTP."""
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

            # Prepare email
            msg = EmailMessage()
            msg['Subject'] = subject
            msg['From'] = f"fundos <{FROM_EMAIL}>"
            msg['To'] = email
            msg.set_content(f"You have been invited by {subadmin_name or 'the team'} to join their subadmin team. Please click on the link to accept: {invite_link}")
            msg.add_alternative(body_html, subtype='html')

            # Send email via SMTP
            try:
                with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=30.0) as server:
                    server.starttls()
                    server.login(self.smtp_username, self.smtp_password)
                    server.send_message(msg)
                logger.info(f"Invitation email sent successfully to {email}")
            except smtplib.SMTPException as e:
                logger.error(f"SMTP error while sending invitation email: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Failed to send invitation email: {str(e)}")

            return {
                "message": "Invitation sent successfully",
                "success": True
            }

        except Exception as e:
            logger.error(f"Failed to send invitation email: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to send invitation email: {str(e)}")
        
    async def send_invitation_to_subadmin(
        self, 
        email: EmailStr, 
        invite_code: str,
        user_name: str = "",
        password: str = "",
        apk_link: str = "https://example.com/invite"
    ) -> Any: 
        """Send an invitation email using Zoho ZeptoMail SMTP."""
        try:
            invite_link = f"{apk_link}?invite_code={invite_code}&email={email}"
            subject = "You have been invited to join a subadmin team"
            body_html = f"""
                <div>
                    <p>Hi {user_name or 'User'},</p>
                    <p>You have been invited by Team FundOS to join as a fund manager.</p>
                    <p>Please click on the following link to accept the invitation: <a href="{invite_link}">{invite_link}</a></p>
                    <p>Thank you,</p>
                    <p>Best regards,<br>{'FundOS'}</p>
                </div>
            """

            # Prepare email
            msg = EmailMessage()
            msg['Subject'] = subject
            msg['From'] = f"fundos <{FROM_EMAIL}>"
            msg['To'] = email
            msg.set_content(f"You have been invited by {'Team FundOS'} to join as a fund manager.\n Here are your credentials:\n Username: {user_name}\n Password: {password}\n Share this Invite code to Onboard investors")
            msg.add_alternative(body_html, subtype='html')

            # Send email via SMTP
            try:
                with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=30.0) as server:
                    server.starttls()
                    server.login(self.smtp_username, self.smtp_password)
                    server.send_message(msg)
                logger.info(f"Invitation email sent successfully to {email}")
            except smtplib.SMTPException as e:
                logger.error(f"SMTP error while sending invitation email: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Failed to send invitation email: {str(e)}")

            return {
                "message": "Invitation sent successfully",
                "success": True
            }

        except Exception as e:
            logger.error(f"Failed to send invitation email: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to send invitation email: {str(e)}")