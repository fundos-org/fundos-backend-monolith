from fastapi import HTTPException
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from src.logging.logging_setup import get_logger # assuming you have a logger setup
from pydantic import EmailStr
from src.models.user import User, investorType
from src.utils.dependencies import get_user
from uuid import UUID
from src.services.s3 import S3Service
from typing import Dict, Any

logger = get_logger(__name__) 

s3_service = S3Service(bucket_name="")

class DummyService:
    def __init__(self):
        self.bucket_name = ""
        self.folder_prefix = ""
  
    async def verify_invitation_code(self, invitation_code: str, session: AsyncSession) -> Dict[str, Any]:

        try: 
            if invitation_code == "fundos": 
                user = User(invitation_code=invitation_code, onboarding_status= "Invitation_verified")
                session.add(user)
                await session.commit()
                await session.refresh(user) 

                return {
                    "success": True,
                    "user_id": user.id
                }
            
            else: 
                return {
                    "success": False, 
                }
        except Exception as e: 
            logger.error(f"Request failed: {e}")
            raise HTTPException(status_code=500, detail="Internal request error")

    async def send_phone_otp(self, phone_num: str) -> dict:

        try:
            return {
                "message" : "otp sent", 
                "otp" : "123456" 
            }  

        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise HTTPException(status_code=500, detail="Internal request error")
        
    async def verify_phone_otp(self, otp_code: str) -> dict: 

        try: 
            if otp_code == "123456" :
                return {
                    "message" : "otp code matched",
                    "success" : True
                }
            
        except Exception as e : 
            logger.error(f"Request failed: {e}")
            raise HTTPException(status_code=500, detail="Internal request error") 
        
    async def set_user_details(self, user_id: str, first_name: str, last_name: str) -> dict:
        
        try:
            user: User = get_user(user_id=user_id)
            user.first_name = first_name
            user.last_name = last_name

            await self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)

            return {
                "message": "User details updated successfully",
                "user_id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name
            }
        except Exception as e:
            await self.session.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to update user details: {str(e)}")
        
    async def send_email_otp(self, email: EmailStr) -> dict:

        try:
            return {
                "message" : "otp sent", 
                "otp" : "123456" 
            }  

        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise HTTPException(status_code=500, detail="Internal request error")
        
    async def verify_email_otp(self, otp_code: str) -> dict: 

        try: 
            if otp_code == "123456" :
                return {
                    "message" : "otp code matched",
                    "success" : True
                }
            
        except Exception as e : 
            logger.error(f"Request failed: {e}")
            raise HTTPException(status_code=500, detail="Internal request error") 
        
    async def choose_investor_type(self, user_id, investor_type:investorType) -> any :
        
        try:
            user: User = get_user(user_id= user_id)
            user.investor_type = investor_type

            await self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)

            return {
                "message": "Investor Type updated successfully",
                "user_id": user.id
            }

        except Exception as e:
            await self.session.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to update user details: {str(e)}")
        
    async def declaration_accepted( self, user_id: str, declaration_accepted: bool) -> any : 

        try: 
            user: User = get_user(user_id=user_id) 

            user.declaration_accepted = declaration_accepted
            await self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user) 

            return {
                "message": "User details updated successfully",
                "user_id": user.id,
                "declaration_accepted": f"{declaration_accepted}",
            }

        except Exception as e:
            await self.session.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to update user details: {str(e)}")
        
    async def set_professional_background( self, user_id: str, occupation: str, income_source: float, annual_income: float, capital_commitment: float) -> any : 

        try: 
            user: User = get_user(user_id=user_id) 

            user.income_source = income_source
            user.annual_income = annual_income
            user.capital_commitment = capital_commitment
            user.occupation  = occupation 

            await self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user) 

            return {
                "message": "User professional details updated successfully",
                "user_id": user.id,
            }

        except Exception as e:
            await self.session.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to update user details: {str(e)}")
        
    async def contribution_agreement(self, user_id: UUID, agreement_signed: bool ) -> dict :

        try: 
            user: User = get_user(user_id=user_id) 

            user.agreement_signed = agreement_signed

            await self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user) 

            return {
                "message": "User signed agreement ",
                "user_id": user.id,
            }

        except Exception as e:
            await self.session.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to update user details: {str(e)}")
        
    async def upload_photograph(self, user_id: UUID, file: UploadFile ) -> dict :

        try: 
            user: User = get_user(user_id=user_id) 
            image_url: str = s3_service.upload_and_get_url(
                file = file,
                bucket_name = self.bucket_name,
                folder_prefix = self.folder_prefix
            )

            user.profile_image_url = image_url

            await self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user) 

            return {
                "message": "User image uploaded successfully ",
                "user_id": user.id,
            }

        except Exception as e:
            await self.session.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to update user details: {str(e)}")
        



        


