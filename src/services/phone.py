import boto3
import redis
import random
import string
from fastapi import HTTPException
from src.logging.logging_setup import get_logger

logger = get_logger(__name__)

AWS_REGION = "ap-south-1"
REDIS_HOST = "redis"
REDIS_PORT = 6379
REDIS_DB = 0
CACHE_TTL = 300

class PhoneService:
    def __init__(self):
        self.sns_client = boto3.client("sns", region_name=AWS_REGION)
        self.redis = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)

    def _generate_otp(self, length: int = 6) -> str:
        return ''.join(random.choices(string.digits, k=length))

    def _get_otp_cache_key(self, phone_number: str) -> str:
        return f"otp:phone:{phone_number}"

    async def send_phone_otp(self, phone_number: str) -> dict:
        try:
            if not phone_number.startswith("+") or len(phone_number) < 10:
                raise HTTPException(status_code=400, detail="Invalid phone number format")
            otp = self._generate_otp()
            message = f"Your verification OTP is {otp}. Valid for 5 minutes."
            response = self.sns_client.publish(
                PhoneNumber=phone_number,
                Message=message,
                MessageAttributes={
                    "AWS.SNS.SMS.SenderID": {"DataType": "String", "StringValue": "Fundos"},
                    "AWS.SNS.SMS.SMSType": {"DataType": "String", "StringValue": "Transactional"}
                }
            )
            logger.info(f"SNS response: {response}")
            cache_key = self._get_otp_cache_key(phone_number)
            self.redis.setex(cache_key, CACHE_TTL, otp)
            return {"message": f"OTP sent to {phone_number}", "phone_number": phone_number}
        except Exception as e:
            logger.error(f"Failed to send OTP: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to send OTP")

    async def verify_phone_otp(self, phone_number: str, otp: str) -> dict:
        try:
            cache_key = self._get_otp_cache_key(phone_number)
            cached_otp = self.redis.get(cache_key)
            if not cached_otp:
                raise HTTPException(status_code=400, detail="OTP expired or not found")
            if cached_otp != otp:
                raise HTTPException(status_code=400, detail="Invalid OTP")
            self.redis.delete(cache_key)
            return {"message": "Phone number verified", "phone_number": phone_number}
        except Exception as e:
            logger.error(f"Failed to verify OTP: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to verify OTP")