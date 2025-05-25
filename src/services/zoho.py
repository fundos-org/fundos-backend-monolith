import httpx
import os
import json
import redis
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.user import User
from src.logging.logging_setup import get_logger
from datetime import datetime
from uuid import UUID
from num2words import num2words
from src.configs.configs import zoho_configs

# Configure logging
logger = get_logger(__name__)

ZOHO_BASE_URL = "https://sign.zoho.in/api/v1"
ZOHO_AUTH_URL = "https://accounts.zoho.in/oauth/v2/token"
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = 6379
REDIS_DB = 0
CACHE_TTL = 604800  # 7 days for Zoho metadata

class ZohoService:
    def __init__(self):
        self.base_url = ZOHO_BASE_URL
        self.auth_url = ZOHO_AUTH_URL
        self.client_id = zoho_configs.zoho_client_id or os.getenv("ZOHO_CLIENT_ID")
        self.client_secret = zoho_configs.zoho_client_secret or os.getenv("ZOHO_CLIENT_SECRET")
        self.refresh_token = zoho_configs.zoho_refresh_token or os.getenv("ZOHO_REFRESH_TOKEN")
        self.redirect_uri = zoho_configs.zoho_redirect_uri or os.getenv("ZOHO_REDIRECT_URI")
        self.redis = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True
        )

    def _get_cache_key(self, user_id: str, key: str) -> str:
        """Generate user-specific Redis cache key."""
        return f"zoho:{user_id}:{key}"

    async def get_access_token(self) -> str:
        """Generate or retrieve cached Zoho access token."""
        cache_key = self._get_cache_key("global", "access_token")
        cached_token = self.redis.get(cache_key)
        if cached_token:
            logger.info("Using cached Zoho access token")
            return cached_token

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.auth_url,
                    data={
                        "refresh_token": self.refresh_token,
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "redirect_uri": self.redirect_uri,
                        "grant_type": "refresh_token"
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                if response.status_code != 200:
                    logger.error(f"Failed to get Zoho token: {response.status_code} {response.text}")
                    raise HTTPException(status_code=response.status_code, detail="Failed to get Zoho token")

                data = response.json()
                token = data.get("access_token")
                if not token:
                    logger.error("No access token in response")
                    raise HTTPException(status_code=500, detail="No access token received")

                # Cache token
                self.redis.setex(cache_key, data.get("expires_in", 3600), token)
                logger.info("Zoho access token cached")
                return token
        except Exception as e:
            logger.error(f"Error generating Zoho token: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error generating Zoho token: {str(e)}")

    async def create_document_from_template(self, user_id: str, session: AsyncSession) -> dict:
        """Create a document from a Zoho Sign template with user data."""
        try:
            user_id_uuid = UUID(user_id)
        except ValueError:
            logger.error(f"Invalid user_id format: {user_id}")
            raise HTTPException(status_code=400, detail="Invalid user_id format")

        user = await session.get(User, user_id_uuid)
        if not user:
            logger.error(f"User not found: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")

        token = await self.get_access_token()
        day = f"{datetime.now().day:02d}"
        month = datetime.now().strftime("%B")
        year = str(datetime.now().year)
        date = f"{month} {day} {year}"
        capital_commitment_word = num2words(
            number=float(user.capital_commitment), 
            lang="en_IN", 
            to="currency", 
            currency = "INR") if user.capital_commitment else ""

        payload = {
            "templates": {
                "field_data": {
                    "field_text_data": {
                        "day": day,
                        "year": year,
                        "date": date,
                        "month": month,
                        "fullName": f"{user.first_name} {user.last_name}" if user.first_name and user.last_name else "",
                        "lastName": user.last_name or "",
                        "email": user.email or "",
                        "capitalCommitmentAmount": str(user.capital_commitment) if user.capital_commitment else "",
                        "capitalCommitmentWord": capital_commitment_word
                    },
                    "field_boolean_data": {},
                    "field_date_data": {},
                    "field_radio_data": {},
                    "field_checkboxgroup_data": {}
                },
                "notes": "",
                "actions": [
                    {
                        "recipient_name": f"{user.first_name} {user.last_name}" if user.first_name and user.last_name else "Investor",
                        "recipient_email": user.email,
                        "action_id": "80016000000046056",
                        "signing_order": 1,
                        "role": "Applicant",
                        "verify_recipient": False,
                        "private_notes": ""
                    },
                    {
                        "recipient_name": "Amit",
                        "recipient_email": "amit@fundos.solutions",
                        "action_id": "80016000000081530",
                        "signing_order": 2,
                        "role": "Signatory",
                        "verify_recipient": False,
                        "private_notes": ""
                    },
                    {
                        "recipient_name": "Iswar",
                        "recipient_email": "ishwarkoki@gmail.com",
                        "action_id": "80016000000081528",
                        "signing_order": 3,
                        "role": "Signatory",
                        "verify_recipient": False,
                        "private_notes": ""
                    }
                ]
            }
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/templates/{os.getenv('MCA_TEMPLATE_ID')}/createdocument",
                    headers={"Authorization": f"Zoho-oauthtoken {token}", "Content-Type": "application/json"},
                    json=payload
                )
                if response.status_code != 200:
                    logger.error(f"Failed to create document: {response.status_code} {response.text}")
                    raise HTTPException(status_code=response.status_code, detail="Failed to create document")

                data = response.json()
                request_id = data["requests"].get("request_id")
                document_id = data["requests"].get("document_ids", [{}])[0].get("document_id")
                action_ids = [action["action_id"] for action in data["requests"].get("actions", [])]

                # Cache metadata in Redis
                metadata = {
                    "request_id": request_id,
                    "document_id": document_id,
                    "action_ids": action_ids,
                    "is_signed": False
                }
                self.redis.setex(
                    self._get_cache_key(user_id, "metadata"),
                    CACHE_TTL,
                    json.dumps(metadata)
                )
                logger.info(f"Cached Zoho metadata for user_id: {user_id}")

                # Update onboarding_status
                user.onboarding_status = "Document Created"
                session.add(user)
                await session.commit()
                await session.refresh(user)

                return metadata
        except Exception as e:
            logger.error(f"Error creating document: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error creating document: {str(e)}")

    async def apply_estamp(self, user_id: UUID, session: AsyncSession) -> dict:
        """Apply e-stamp to the MCA document."""
        
        user = await session.get(User, user_id)
        if not user:
            logger.error(f"User not found: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")

        # Retrieve MCA metadata from Redis
        metadata_key = self._get_cache_key(user_id, "metadata")
        metadata = self.redis.get(metadata_key)
        if not metadata:
            logger.error(f"Missing metadata for user_id: {user_id}")
            raise HTTPException(status_code=400, detail="Missing document metadata")

        metadata = json.loads(metadata)
        request_id = metadata["request_id"]
        document_id = metadata["document_id"]

        token = await self.get_access_token()
        # Use FormData for multipart/form-data
        from io import BytesIO
        form_data = {
            "data": json.dumps({
                "requests": {
                    "request_name": f"MCA Document for {user.first_name} {user.last_name}",
                    "document_ids": [
                        {
                            "document_id": document_id,
                            "document_order": 0,
                            "estamping_request": {
                                "stamp_duty_paid_by": "First Party",
                                "stamp_state": "DL",
                                "stamp_amount": os.getenv("STAMP_AMOUNT") or "100",
                                "document_category": os.getenv("DOCUMENT_CATEGORY") or "1",
                                "duty_payer_phone_number": "7400160348",
                                "first_party_name": "Thirty3art Ventures LLP and Ors",
                                "second_party_name": "Mitcon Credentia Trusteeship S Ltd", 
                                "consideration_amount": os.getenv("STAMP_AMOUNT") or "100",
                                "document_reference_no": "111",
                                "duty_payer_email_id": "Artventures.operations@gmail.com",
                                "first_party_details": {
                                    "first_party_entity_type": "Individual",
                                    "first_party_id_type": "UID",
                                    "first_party_id_number": "661933060650"
                                },
                                "first_party_address": {
                                    "country": "India",
                                    "street_address": " C-203, Badhwar Apartment, South West Delhi",
                                    "city": "New Delhi",
                                    "state": "DL",
                                    "pincode": "110075"
                                },
                                "second_party_address": {
                                    "country": "India",
                                    "street_address": "1402/1403 Dalamal Towers, 211 Free Press Journal Marg",
                                    "city": "Mumbai",
                                    "state": "MH",
                                    "pincode": "400021"
                                }
                            }
                        }
                    ]
                }
            })
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.put(
                    f"{self.base_url}/requests/{request_id}",
                    headers={"Authorization": f"Zoho-oauthtoken {token}"},
                    data=form_data
                )
                if response.status_code != 200:
                    logger.error(f"Failed to apply e-stamp: {response.status_code} {response.text}")
                    raise HTTPException(status_code=response.status_code, detail="Failed to apply e-stamp")
            
                data = response.json()
                # Update onboarding_status
                user.onboarding_status = "E-Stamp Applied"
                session.add(user)
                await session.commit()
                await session.refresh(user)

                return {
                    "data": data,
                    "request_id": request_id,
                    "document_id": document_id, 
                    "success": True
                }
        except Exception as e:
            logger.error(f"Error applying e-stamp: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error applying e-stamp: {str(e)}")

    async def send_document_for_signing(self, user_id: str, session: AsyncSession) -> dict:
        """Send the e-stamped MCA document to three signers."""
        metadata_key = self._get_cache_key(user_id, "metadata")
        metadata = self.redis.get(metadata_key)
        if not metadata:
            logger.error(f"Missing metadata for user_id: {user_id}")
            raise HTTPException(status_code=400, detail="Missing document metadata")

        metadata = json.loads(metadata)
        request_id = metadata["request_id"]
        action_ids = metadata["action_ids"]

        token = await self.get_access_token()
        payload = {
            "requests": {
                "actions": [
                    {"action_id": action_id, "action_type": "SIGN"} for action_id in action_ids
                ]
            }
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/requests/{request_id}/submit",
                    headers={"Authorization": f"Zoho-oauthtoken {token}", "Content-Type": "application/json"},
                    json=payload
                )
                if response.status_code != 200:
                    logger.error(f"Failed to send document: {response.status_code} {response.text}")
                    raise HTTPException(status_code=response.status_code, detail="Failed to send document")

                user = await session.get(User, UUID(user_id))
                if user:
                    user.onboarding_status = "Sent for Signing"
                    session.add(user)
                    await session.commit()
                    await session.refresh(user)

                return response.json()
        except Exception as e:
            logger.error(f"Error sending document: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error sending document: {str(e)}")

    async def handle_webhook(self, payload: dict, session: AsyncSession) -> dict:
        """Handle Zoho Sign webhook for DOCUMENT_COMPLETED."""
        notification_type = payload.get("notifications", {}).get("operation_type")
        if notification_type != "DOCUMENT_COMPLETED":
            logger.info(f"Ignoring non-completed event: {notification_type}")
            return {"status": "ignored"}

        request_id = payload["requests"].get("request_id")
        action_ids = [action["action_id"] for action in payload["requests"].get("actions", [])]
        document_id = payload["requests"].get("document_ids", [{}])[0].get("document_id")

        if len(action_ids) != 3:
            logger.error(f"Expected 3 signers, found {len(action_ids)} for request_id: {request_id}")
            return {"status": "error", "detail": "Incomplete signatures"}

        user_id = None
        for key in self.redis.keys("zoho:*:metadata"):
            metadata = json.loads(self.redis.get(key) or "{}")
            if metadata.get("request_id") == request_id:
                user_id = key.split(":")[1]
                break

        if not user_id:
            logger.error(f"No user found for request_id: {request_id}")
            raise HTTPException(status_code=404, detail="User not found")

        user = await session.get(User, UUID(user_id))
        if not user:
            logger.error(f"User not found in database: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")

        token = await self.get_access_token()
        async with httpx.AsyncClient(timeout=30.0) as client:
            pdf_response = await client.get(
                f"{self.base_url}/requests/{request_id}/pdf",
                headers={"Authorization": f"Zoho-oauthtoken {token}"}
            )
            pdf_data = pdf_response.content

        public_dir = os.path.join(os.getcwd(), "public", "signed_document")
        os.makedirs(public_dir, exist_ok=True)
        file_path = os.path.join(public_dir, f"{request_id}-{int(datetime.now().timestamp())}.pdf")
        with open(file_path, "wb") as f:
            f.write(pdf_data)

        user.signed_document = f"/signed_document/{os.path.basename(file_path)}"
        user.onboarding_status = "Completed"
        user.agreement_signed = True
        session.add(user)
        await session.commit()
        await session.refresh(user)

        metadata_key = self._get_cache_key(user_id, "metadata")
        metadata = json.loads(self.redis.get(metadata_key) or "{}")
        metadata["is_signed"] = True
        self.redis.setex(metadata_key, CACHE_TTL, json.dumps(metadata))

        logger.info(f"User {user_id} onboarded successfully for request_id: {request_id}")
        return {"success": True, "user_id": user_id}