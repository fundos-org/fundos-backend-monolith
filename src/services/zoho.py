import re
from tempfile import SpooledTemporaryFile
from typing import Any, Dict
import httpx
import os
import json
import redis
from fastapi import HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.deal import Deal
from src.services.s3 import S3Service
from src.models.user import User, OnboardingStatus
from src.models.kyc import KYC
from src.logging.logging_setup import get_logger
from datetime import datetime
from uuid import UUID
from num2words import num2words
from src.configs.configs import zoho_configs, redis_configs, aws_config

# Configure logging
logger = get_logger(__name__)

ZOHO_BASE_URL = zoho_configs.zoho_base_url 
ZOHO_AUTH_URL = zoho_configs.zoho_auth_url
REDIS_HOST = redis_configs.redis_host 
REDIS_PORT = redis_configs.redis_port
REDIS_DB = redis_configs.redis_db
CACHE_TTL = redis_configs.redis_cache_ttl  # 7 days for Zoho metadata

class ZohoService:
    def __init__(self):
        self.base_url = ZOHO_BASE_URL
        self.auth_url = ZOHO_AUTH_URL
        self.client_id = zoho_configs.zoho_client_id 
        self.client_secret = zoho_configs.zoho_client_secret
        self.refresh_token = zoho_configs.zoho_refresh_token
        self.redirect_uri = zoho_configs.zoho_redirect_uri 
        self.drawdown_template_id = zoho_configs.drawdown_template_id
        self.management_fee_percentage = 2
        self.gst_percentage = 18
        self.redis = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True
        )
        self.s3_service = S3Service(bucket_name="fundos-dev-bucket", region_name="ap-south-1")

    def _get_cache_key(
        self, 
        user_id: str, 
        key: str
    ) -> str:
        """Generate user-specific Redis cache key."""
        return f"zoho:{user_id}:{key}"

    async def get_access_token(
        self
    ) -> str:
        """Generate or retrieve cached Zoho access token."""
        cache_key = self._get_cache_key("global", "access_token")
        cached_token = self.redis.get(cache_key)
        if cached_token:
            logger.info("Using cached Zoho access token")
            return cached_token

        params = {
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "grant_type": "refresh_token"
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url=self.auth_url,
                    params=params,
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

    async def get_mca_payload(
        self, 
        user: User, 
        kyc: KYC
    ) -> dict:
        """Generate Zoho Sign payload for MCA template based on provided JSON structure."""
        # Calculate date fields
        current_date = datetime.now()
        day = f"{current_date.day:02d}"
        month = current_date.strftime("%B")
        year = str(current_date.year)
        date = f"{month} {day} {year}"
        match = re.match(r"(S/O|D/O|C/O)\s+(.*)", user.care_of, re.IGNORECASE)
        father_name = match.group(2) if match else None
        date_of_birth = user.date_of_birth
        dob_obj = datetime.strptime(date_of_birth, "%d-%m-%Y")
        formatted_dob = dob_obj.strftime("%b %d %Y")
        capital_commitment = float(user.capital_commitment) 

        if not capital_commitment:
            raise HTTPException(status_code=400, detail="Capital commitment is required")


        # Calculate capital commitment in words
        capital_commitment_in_word = (
            num2words(
                number=float(user.capital_commitment),
                lang="en_IN",
                to="currency",
                currency="INR"
            )
        )

        payload = {
            "templates": {
                "field_data": {
                    "field_text_data": {
                        "day": day,
                        "month": month,
                        "year": year,
                        "name": user.full_name, 
                        "address": user.address,
                        "phone": user.phone_number, 
                        "email": user.email,
                        "father_name": father_name, 
                        "entity_type": user.investor_type,
                        "law": "Not Applicable",
                        "pan_number": kyc.pan_number,
                        "phone_number": user.phone_number,
                        "capital_commitment": str(capital_commitment),
                        "capital_commitment_words": capital_commitment_in_word,
                        "resident": user.country,
                        "tax_identity_number": "Not Applicable",
                        "place_of_birth": "Not Applicable",
                    },
                    "field_boolean_data": {},
                    "field_date_data": {
                        "date": date,
                        "date_of_birth": formatted_dob
                    },
                    "field_radio_data": {},
                    "field_checkboxgroup_data": {}
                },
                "notes": "",
                "actions": [
                    {
                        "recipient_name": user.full_name if user.full_name else "Investor",
                        "recipient_email": user.email,
                        "action_id": "80016000000197416",
                        "action_type": "SIGN",
                        "signing_order": 1,
                        "role": "Applicant",
                        "verify_recipient": False,
                        "private_notes": ""
                    },
                    {
                        "recipient_name": "Amit",
                        "recipient_email": "amit@fundos.solutions",
                        "action_id": "80016000000197418",
                        "action_type": "SIGN",
                        "signing_order": 2,
                        "role": "Signatory",
                        "verify_recipient": False,
                        "private_notes": ""
                    },
                    {
                        "recipient_name": "Iswar",
                        "recipient_email": "ishwarkoki@gmail.com",
                        "action_id": "80016000000207922",
                        "action_type": "SIGN",
                        "signing_order": 3,
                        "role": "Signatory",
                        "verify_recipient": False,
                        "private_notes": ""
                    }
                ]
            }
        }

        return payload
    
    async def create_document_from_template(
        self, 
        user_id: UUID, 
        session: AsyncSession
    ) -> dict:
        """Create a document from a Zoho Sign template with user data."""
        user = await session.get(User, user_id)
        stmt = select(KYC).where(KYC.user_id == user_id)
        db_result = await session.execute(stmt)
        kyc = db_result.scalars().first()

        if not user or not kyc:
            logger.error(f"User not found: {user_id} or kyc record not found: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")

        # Generate payload using get_payload
        payload = await self.get_mca_payload(
            user=user, 
            kyc=kyc
        )

        token = await self.get_access_token()
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/templates/{zoho_configs.contribution_template_id}/createdocument",
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

                return metadata
        except Exception as e:
            logger.error(f"Error creating document: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error creating document: {str(e)}")

    async def apply_estamp(
        self, 
        user_id: UUID, 
        session: AsyncSession
    ) -> dict:
        """Apply e-stamp to the MCA document."""
        user = await session.get(User, user_id)
        if not user:
            logger.error(f"User not found: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")

        # Retrieve MCA metadata from Redis
        metadata_key = self._get_cache_key(user_id, "metadata") #self._get_cache_key(user_id, "metadata")
        metadata = self.redis.get(metadata_key)
        if not metadata:
            logger.error(f"Missing metadata for user_id: iswar")
            raise HTTPException(status_code=400, detail="Missing document metadata")

        metadata = json.loads(metadata)
        request_id = metadata["request_id"]
        document_id = metadata["document_id"]

        # set zoho request id value in the db
        user.zoho_request_id = request_id
        await session.commit()
        await session.refresh(user)

        token = await self.get_access_token()
        form_data = {
            "data": json.dumps({
                "requests": {
                    "request_name": f"MCA Document for {user.full_name}", #{user.first_name} {user.last_name}
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
                                    "street_address": "C-203, Badhwar Apartment, South West Delhi",
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

                response_data = {
                    "data": data,
                    "request_id": request_id,
                    "document_id": document_id,
                    "success": True
                }

            return response_data
            
        except Exception as e:
            session.close()
            logger.error(f"Error applying e-stamp: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error applying e-stamp: {str(e)}")

    async def send_document_for_signing(
        self, 
        user_id: str, 
        session: AsyncSession
    ) -> dict:
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
                    user.onboarding_status = OnboardingStatus.Zoho_Document_Sent.name
                    session.add(user)
                    await session.commit()
                    await session.refresh(user)

                return response.json()
        except Exception as e:
            logger.error(f"Error sending document: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error sending document: {str(e)}")
        
    async def download_signed_document(
        self, 
        request_id: str, 
        action_id: str, 
        session: AsyncSession
    ) -> dict:
        """Download a signed Zoho Sign document and upload to S3."""
        # Find user_id from Redis metadata
        user_id = None
        for key in self.redis.keys("zoho:*:metadata"):
            metadata = json.loads(self.redis.get(key) or "{}")
            if metadata.get("request_id") == request_id and action_id in metadata.get("action_ids", []):
                user_id = key.split(":")[1]
                break

        if not user_id:
            logger.error(f"No user found for request_id: {request_id}, action_id: {action_id}")
            raise HTTPException(status_code=404, detail="User not found for request_id and action_id")

        user = await session.get(User, UUID(user_id))
        if not user:
            logger.error(f"User not found in database: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")

        token = await self.get_access_token()
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.base_url}/requests/{request_id}/pdf",
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code != 200:
                logger.error(f"Failed to download PDF: {response.status_code} {response.text}")
                raise HTTPException(status_code=response.status_code, detail="Failed to download PDF")

            pdf_data = response.content

        # Create an UploadFile object from PDF bytes
        with SpooledTemporaryFile(max_size=10_000_000, mode='wb') as temp_file:
            temp_file.write(pdf_data)
            temp_file.seek(0)
            upload_file = UploadFile(
                filename=f"{user_id}-{request_id}-{int(datetime.now().timestamp())}.pdf",
                file=temp_file,
                content_type="application/pdf"
            )
            # Upload to S3
            object_key = await self.s3_service.upload_and_get_key(
                object_id=UUID(user_id),
                file=upload_file,
                bucket_name="fundos-dev-bucket",
                folder_prefix="signed_documents/"
            )

        # Update user record
        user.mca_key = object_key
        session.add(user)
        try:
            await session.commit()
            await session.refresh(user)
        except Exception as e:
            logger.error(f"Failed to update user: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to update user: {str(e)}")

        # Update Redis metadata
        metadata_key = self._get_cache_key(user_id, "metadata")
        metadata = json.loads(self.redis.get(metadata_key) or "{}")
        metadata["is_signed"] = True
        self.redis.setex(metadata_key, CACHE_TTL, json.dumps(metadata))

        logger.info(f"Signed document uploaded to S3 for user_id: {user_id}, request_id: {request_id}")
        return {"success": True, "user_id": user_id, "file_path": user.mca_key}
    
    async def handle_webhook(
        self, 
        payload: dict, 
        session: AsyncSession
    ) -> dict:
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
        user.onboarding_status = "COMPLETED"
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
    
    async def get_drawdown_payload(
        self, 
        user: User, 
        deal: Deal, 
        investment_amount: float
    ) -> Dict:
        """
        Construct and return the drawdown notice payload with dynamic data
        pulled from the User and Deal models.
        """

        try:
            # Sample extraction logic — adjust field names as per actual model
            investor_name = user.full_name
            investor_email = user.email
            investment_scheme = "Sample Scheme" # need to add a field for this in deal model
            company_name = deal.company_name
            capital_commitment = user.capital_commitment
            investment_amount_str = f"{investment_amount:,.2f}"
            drawdown_amount = user.drawdown_amount or 0

            # calculate management fee
            investment_commission = investment_amount * (self.management_fee_percentage / 100)
            gst = investment_commission * (self.gst_percentage / 100)
            total_fee = investment_commission + gst 

            management_fee_str = f"{total_fee:,.2f}" # management fee

            # calculate total payable
            total_payable = investment_amount + total_fee
            total_payable_str = f"{total_payable:,.2f}" # total payable

            capital_commitment_str = f"{capital_commitment:,.2f}"

            drawdown_so_far = drawdown_amount + total_payable # need to add a field for this in user model : user.drawdown_amount
            drawdown_so_far = f"{drawdown_so_far:,.2f}"

            undrawn_capital_commitment = capital_commitment - total_payable 
            undrawn_commitment = f"{undrawn_capital_commitment:,.2f}"

            # Construct the payload
            payload = {
                "templates": {
                    "field_data": {
                        "field_text_data": {
                            "investor": investor_name,
                            "investment_scheme": investment_scheme,
                            "company_name": company_name,
                            "Investment_amount": investment_amount_str,
                            "management_fee": management_fee_str,
                            "total_payable": total_payable_str,
                            "capital_commitment": capital_commitment_str,
                            "drawdown_so_far": drawdown_so_far,
                            "undrawn_capital_commitment": undrawn_commitment,
                        },
                        "field_boolean_data": {},
                        "field_date_data": {
                            "date": datetime.today().strftime("%d %B %Y")  # Example: "04 June 2025"
                        },
                        "field_radio_data": {},
                        "field_checkboxgroup_data": {},
                    },
                    "notes": "",
                    "actions": [
                        {
                            "recipient_name": investor_name,
                            "recipient_email": investor_email,
                            "action_id": "80016000000209128",
                            "action_type": "SIGN",
                            "signing_order": 1,
                            "role": "Investor",
                            "verify_recipient": False,
                            "private_notes": ""
                        }
                    ]
                }
            }

            return payload
        
        except AttributeError as e:
            logger.error(f"AttributeError: Missing or incorrect attribute in the database model, details: {e}")
            raise HTTPException(status_code=500, detail="Missing or incorrect attribute in the database model.")
        
        except TypeError as e:
            logger.error(f"TypeError: Incorrect data type for the attribute, details: {e}")
            raise HTTPException(status_code=500, detail=f"Incorrect data type for the attribute, details: {e}")
        
        except Exception as e:
            logger.error(f"Error occurred while generating drawdown payload: {e}")
            raise HTTPException(status_code=500, detail="Error occurred while generating drawdown payload")
        
    async def send_drawdown_notice(
        self, 
        user_id: UUID, 
        deal_id: UUID,
        investment_amount: float,
        session: AsyncSession
    ) -> Any: 
        try:
            user = await session.get(User, user_id)
            deal = await session.get(Deal, deal_id)
            
            if not user or not deal:
                raise HTTPException(status_code=404, detail="User or deal not found")
            
            token = await self.get_access_token()
            if not token:
                raise HTTPException(status_code=401, detail="Unauthorized")
            
            payload = await self.get_drawdown_payload(
                user=user, 
                deal=deal,
                investment_amount=investment_amount
            )
            
            if not payload:
                raise HTTPException(status_code=500, detail="Failed to generate drawdown payload")
            
            logger.info(f"Sending drawdown notice for user_id: {user_id}, deal_id: {deal_id}")

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/templates/{self.drawdown_template_id}/createdocument",
                    headers={
                        "Authorization": f"Zoho-oauthtoken {token}", 
                        "Content-Type": "application/json"
                    },
                    json=payload
                )
                if response.status_code != 200:
                    logger.error(f"Failed to create document: {response.status_code} {response.text}")
                    raise HTTPException(status_code=response.status_code, detail="Failed to create document")
                
                data = response.json()
                return data
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create drawdown: {str(e)}")
            
        finally:
            await session.close()

    async def get_document_status(
        self, 
        request_id: str, 
    ) -> Dict: 
        try:
            token = await self.get_access_token()
            if not token:
                raise HTTPException(status_code=401, detail="Unauthorized")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/requests/{request_id}",
                    headers={
                        "Authorization": f"Zoho-oauthtoken {token}"
                    }
                )
                if response.status_code != 200:
                    raise HTTPException(status_code=response.status_code, detail="Failed to get document status")
                
                data = response.json()
                requests_data = data.get("requests", {})
                
                # Extract and sanitize fields from requests
                response_data = {
                    "request_id": str(data.get("request_id", "")),
                    "sent_status": str(data.get("status", "")),
                    "message": str(data.get("message", "")),
                    "request_status": str(requests_data.get("request_status", "")),
                    "is_deleted": bool(requests_data.get("is_deleted", False)),
                    "request_name": str(requests_data.get("request_name", "")),
                    "expiration_days": int(requests_data.get("expiration_days", 0)),
                    "sign_percentage": float(requests_data.get("sign_percentage", 0.0)),
                    "owner_email": str(requests_data.get("owner_email", "")),
                    "actions": [
                        {
                            "recipient_email": str(action.get("recipient_email", "")),
                            "recipient_phone_number": str(action.get("recipient_phonenumber", "")),
                            "recipient_name": str(action.get("recipient_name", "")),
                            "delivery_mode": str(action.get("delivery_mode", "")),
                            "action_status": str(action.get("action_status", ""))
                        } for action in requests_data.get("actions", [])
                    ]
                }
                
                return response_data
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get document status: {str(e)}")
        
    async def download_mca_pdf(
        self,
        user_id: str,
        session: AsyncSession
    ) -> Dict[str, Any]: 
        
        try: 
            token = await self.get_access_token()
            if not token:
                raise HTTPException(status_code=401, detail="Unauthorized: token not found")
            
            user_uuid = UUID(user_id)
            if not user_uuid:
                raise HTTPException(status_code=400, detail=f"Invalid user UUID: {user_id}")
            
            user = await session.get(User, user_uuid)
            if not user:
                raise HTTPException(status_code=404, detail=f"User not found: {user_id}")
            
            if not user.zoho_request_id:
                raise HTTPException(status_code=404, detail=f"request id for document not found: {user_id}")

            request_id = user.zoho_request_id
            logger.info(f"request_id for user_id: {user_id} is {request_id}")
            
            async with httpx.AsyncClient(timeout=30.0) as client: 
                response = await client.get(
                    f"{self.base_url}/requests/{request_id}/pdf",
                    headers={
                        "Authorization": f"Zoho-oauthtoken {token}"
                    }
                )
                if response.status_code != 200:
                    raise HTTPException(status_code=response.status_code, detail="Failed to download signed pdf")
                
                pdf_data = response.content
            
            with SpooledTemporaryFile(max_size=10_000_000, mode='wb') as temp_file:
                temp_file.write(pdf_data)
                temp_file.seek(0)
                upload_file = UploadFile(
                    filename=f"{user_id}-{request_id}-{int(datetime.now().timestamp())}.pdf",
                    file=temp_file,
                    content_type="application/pdf"
                )
                # Upload to S3
                object_key = await self.s3_service.upload_and_get_key(
                    object_id=UUID(user_id),
                    file=upload_file,
                    bucket_name=aws_config.aws_bucket,
                    folder_prefix=aws_config.aws_deals_folder
                )
            # Update user record
            user.mca_key = object_key
            await session.commit()
            await session.refresh(user)
            
            return {
                "mca_key": object_key,
                "success": True
            }
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to download signed pdf: {str(e)}")
        
    async def check_document_status_by_user_id(
        self, 
        user_id: str,
        session: AsyncSession
    ) -> Dict[str, Any]:
        try:
            token = await self.get_access_token()
            if not token:
                raise HTTPException(status_code=401, detail="Unauthorized: token not found")
            
            user_uuid = UUID(user_id)
            if not user_uuid:
                raise HTTPException(status_code=400, detail=f"Invalid user UUID: {user_id}")
            
            user = await session.get(User, user_uuid)
            if not user:
                raise HTTPException(status_code=404, detail=f"User not found: {user_id}")
            
            if not user.zoho_request_id:
                raise HTTPException(status_code=404, detail=f"request id for document not found: {user_id}")
            
            request_id = user.zoho_request_id
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/requests/{request_id}",
                    headers={
                        "Authorization": f"Zoho-oauthtoken {token}"
                    }
                )
                if response.status_code != 200:
                    raise HTTPException(status_code=response.status_code, detail="Failed to get document status")
                
                data = response.json()
                requests_data = data.get("requests", {})
                
                # Extract and sanitize fields from requests
                response_data = {
                    "request_id": str(data.get("request_id", "")),
                    "sent_status": str(data.get("status", "")),
                    "message": str(data.get("message", "")),
                    "request_status": str(requests_data.get("request_status", "")),
                    "is_deleted": bool(requests_data.get("is_deleted", False)),
                    "request_name": str(requests_data.get("request_name", "")),
                    "expiration_days": int(requests_data.get("expiration_days", 0)),
                    "sign_percentage": float(requests_data.get("sign_percentage", 0.0)),
                    "owner_email": str(requests_data.get("owner_email", "")),
                    "actions": [
                        {
                            "recipient_email": str(action.get("recipient_email", "")),
                            "recipient_phone_number": str(action.get("recipient_phonenumber", "")),
                            "recipient_name": str(action.get("recipient_name", "")),
                            "delivery_mode": str(action.get("delivery_mode", "")),
                            "action_status": str(action.get("action_status", ""))
                        } for action in requests_data.get("actions", [])
                    ]
                }
                
                return response_data
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to check document status: {str(e)}")