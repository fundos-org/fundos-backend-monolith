import httpx
from fastapi import HTTPException
from src.logging.logging_setup import get_logger
from src.configs.configs import msg91_configs

logger = get_logger(__name__)

MSG91_AUTHKEY = msg91_configs.msg91_authkey
MSG91_SIGNUP_TEMPLATE_ID = msg91_configs.msg91_signup_template_id  
MSG91_SIGNIN_TEMPLATE_ID = msg91_configs.msg91_signin_template_id
MSG91_OTP_API = msg91_configs.msg91_otp_api
MSG91_VERIFY_API = msg91_configs.msg91_verify_api

# Country codes dictionary with expected phone number length (excluding country code)
COUNTRY_CODES = {
    "india": {"code": "91", "phone_length": 10},
    "us": {"code": "1", "phone_length": 10},
    "uk": {"code": "44", "phone_length": 10},
    "uae": {"code": "971", "phone_length": 9},
    "singapore": {"code": "65", "phone_length": 8}
}

class PhoneService:
    def __init__(self):
        self.http_client = httpx.AsyncClient()

    async def send_phone_otp(
        self, 
        phone_number: str, 
        user_name: str,
        country: str = "india", 
        process: str = "signup"
    ) -> dict:
        try:
            # Validate country
            country = country.lower()
            if country not in COUNTRY_CODES:
                raise HTTPException(status_code=400, detail="Unsupported country. Supported: india, us, uk, dubai, singapore")
            
            country_info = COUNTRY_CODES[country]
            country_code = country_info["code"]
            expected_length = country_info["phone_length"]

            # Validate phone number
            if not phone_number.isdigit():
                raise HTTPException(status_code=400, detail="Phone number must contain only digits")
            if len(phone_number) != expected_length:
                raise HTTPException(
                    status_code=400,
                    detail=f"Phone number must be {expected_length} digits for {country.title()}"
                )
            
            phone_with_country_code = country_code + phone_number
            full_phone_number = f"+{phone_with_country_code}"

            payload = {
                "Param1": user_name  # Adjust Param1, Param2 based on your MSG91 template
            }

            params = {
                "template_id": MSG91_SIGNUP_TEMPLATE_ID if process == "signup" else MSG91_SIGNIN_TEMPLATE_ID,
                "mobile": phone_with_country_code,
                "authkey": MSG91_AUTHKEY,
                "realTimeResponse": "true"  # Optional but improves feedback
            }

            response = await self.http_client.post(
                MSG91_OTP_API,
                json=payload,
                params=params,
                headers={"Content-Type": "application/json"}
            )

            response_data = response.json()
            logger.info(f"MSG91 send OTP response: {response_data}")

            if response.status_code != 200 or response_data.get("type") != "success":
                raise HTTPException(status_code=500, detail="Failed to send OTP via MSG91")

            return {
                "message": f"OTP sent to {full_phone_number}", 
                "phone_number": full_phone_number, 
                "success": True
            }

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error while sending OTP: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to send OTP")
        except Exception as e:
            logger.error(f"Unexpected error while sending OTP: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to send OTP")

    async def verify_phone_otp(
        self, 
        phone_number: str, 
        otp: str,
        country: str
    ) -> dict:
        try:
            # Validate country
            country = country.lower()
            if country not in COUNTRY_CODES:
                raise HTTPException(status_code=400, detail="Unsupported country. Supported: india, us, uk, dubai, singapore")
            
            country_info = COUNTRY_CODES[country]
            country_code = country_info["code"]
            expected_length = country_info["phone_length"]

            # Validate phone number
            if not phone_number.isdigit():
                raise HTTPException(status_code=400, detail="Phone number must contain only digits")
            if len(phone_number) != expected_length:
                raise HTTPException(
                    status_code=400,
                    detail=f"Phone number must be {expected_length} digits for {country.title()}"
                )
            
            phone_with_country_code = country_code + phone_number
            full_phone_number = f"+{phone_with_country_code}"

            params = {
                "mobile": phone_with_country_code,
                "otp": otp
            }

            headers = {
                "authkey": MSG91_AUTHKEY
            }

            response = await self.http_client.get(
                MSG91_VERIFY_API,
                params=params,
                headers=headers
            )

            response_data = response.json()
            logger.info(f"MSG91 verify OTP response: {response_data}")

            if response.status_code != 200 or response_data.get("type") != "success":
                return {
                    "message": "Invalid OTP",
                    "success": False
                }
                

            return {
                "message": "Phone number verified",
                "phone_number": full_phone_number, 
                "success": True
            }

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error while verifying OTP: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to verify OTP")
        except Exception as e:
            logger.error(f"Unexpected error while verifying OTP: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to verify OTP")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.http_client.aclose()
