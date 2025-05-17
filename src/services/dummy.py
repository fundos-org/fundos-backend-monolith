from fastapi import HTTPException
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from src.logging.logging_setup import get_logger # assuming you have a logger setup
from pydantic import EmailStr
from src.models.user import User, investorType
from src.models.subadmin import Subadmin
from src.utils.dependencies import get_user
from uuid import UUID
from src.services.s3 import S3Service
from typing import Dict, Any
from datetime import datetime

logger = get_logger(__name__) 

class DummyService:
    def __init__(self):
        self.bucket_name = "fundos-dev-bucket"
        self.folder_prefix = "users/profile_pictures/"
        self.s3_service = S3Service(bucket_name=self.bucket_name, region_name="ap-south-1")
  
    async def verify_invitation_code(
        self, 
        invitation_code: str, 
        session: AsyncSession    
    ) -> Dict[str, Any]:

        try:
            # Check if invitation code exists in Subadmin table
            stmt = select(Subadmin).where(Subadmin.invite_code == invitation_code)
            result = await session.execute(stmt)
            subadmin = result.scalar_one_or_none()

            if subadmin:
                # Create new user with the valid invitation code
                user = User(
                    invitation_code=invitation_code,
                    onboarding_status="Invitation_verified",
                    fund_manager_id=subadmin.id  # Link user to subadmin
                )
                session.add(user)
                await session.commit()
                await session.refresh(user)

                return {
                    "success": True,
                    "user_id": user.id,
                    "fund_manager_id": subadmin.id
                }
            else:
                return {
                    "success": False,
                    "error": "Invalid invitation code"
                }

        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise HTTPException(status_code=500, detail="Internal request error")

    async def send_phone_otp(
        self, 
        phone_number: str
    ) -> dict:

        try:
            return {
                "message" : f"otp sent to: {phone_number}", 
                "otp" : "123456" 
            }  

        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise HTTPException(status_code=500, detail="Internal request error")
        
    async def verify_phone_otp(
        self, 
        user_id: UUID, 
        otp_code: str, 
        phone_number: str, 
        session: AsyncSession
    ) -> dict: 

        try:
            user = await session.get(User, user_id)
            if not user:
                raise HTTPException(status_code=404, detail="Deal not found")

            if otp_code == "123456": 
                user.phone_number = phone_number
                user.updated_at = datetime.now()

                await session.commit()
                await session.refresh(user)

            return {
                "message": "Phone num verified", 
                "user_id": f"{user_id}"
            }
        except HTTPException as he:
            raise he
        except Exception as e:
            logger.error(f"Failed to update company details: {str(e)}")
            await session.rollback()
            raise HTTPException(status_code=500, detail="Internal server error")
        
    async def set_user_details(
        self, 
        user_id: UUID, 
        first_name: str, 
        last_name: str, 
        session: AsyncSession
    ) -> dict:
        
        try:
            user = await get_user(user_id=user_id, session=session)
            user.first_name = first_name
            user.last_name = last_name

            await session.commit()
            await session.refresh(user)

            return {
                "message": "User details updated successfully",
                "user_id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name
            }
        except Exception as e:
            await session.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to update user details: {str(e)}")
        
    async def send_email_otp(
        self, 
        email: EmailStr
    ) -> dict:

        try:
            return {
                "message" : f"otp sent to: {email}", 
                "otp" : "123456" 
            }  

        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise HTTPException(status_code=500, detail="Internal request error")
        
    async def verify_email_otp(
        self, 
        otp: str
    ) -> dict: 

        try: 
            if otp == "123456" :
                return {
                    "message" : "otp code matched",
                    "success" : True
                }
            
        except Exception as e : 
            logger.error(f"Request failed: {e}")
            raise HTTPException(status_code=500, detail="Internal request error") 
        
    async def choose_investor_type(
        self, 
        user_id: UUID, 
        investor_type:investorType, 
        session: AsyncSession
    ) -> any :
        
        try:
            user = await get_user(user_id= user_id, session=session)
            user.investor_type = investor_type

            await session.commit()
            await session.refresh(user)

            return {
                "message": "Investor Type updated successfully",
                "user_id": user.id
            }

        except Exception as e:
            await session.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to update user details: {str(e)}")
        
    async def declaration_accepted( 
        self, 
        user_id: str, 
        declaration_accepted: bool, 
        session: AsyncSession
    ) -> any : 

        try: 
            user = await get_user(user_id=user_id, session=session) 

            user.declaration_accepted = declaration_accepted

            await session.commit()
            await session.refresh(user) 

            return {
                "message": "User details updated successfully",
                "user_id": user.id,
            }

        except Exception as e:
            await session.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to update user details: {str(e)}")
        
    async def set_professional_background( 
        self, 
        user_id: str, 
        occupation: str, 
        income_source: float, 
        annual_income: float, 
        capital_commitment: float, 
        session: AsyncSession
    ) -> any : 

        try: 
            user = await get_user(user_id=user_id, session=session) 

            user.income_source = income_source
            user.annual_income = annual_income
            user.capital_commitment = capital_commitment
            user.occupation  = occupation 

            await session.commit()
            await session.refresh(user) 

            return {
                "message": "User professional details updated successfully",
                "user_id": user.id,
            }

        except Exception as e:
            await session.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to update user details: {str(e)}")
        
    async def contribution_agreement(
        self, 
        user_id: UUID, 
        agreement_signed: bool, 
        session: AsyncSession
    ) -> dict :

        try: 
            user = await get_user(user_id=user_id, session=session) 

            user.agreement_signed = agreement_signed

            await session.commit()
            await session.refresh(user) 

            return {
                "message": "User signed agreement ",
                "user_id": user.id,
            }

        except Exception as e:
            await session.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to update user details: {str(e)}")
        
    async def upload_photograph(
        self, 
        user_id: UUID, 
        file: UploadFile, 
        session: AsyncSession
    ) -> dict:
        """
        Uploads a user profile photograph to S3 and updates the user's profile_image_url in the database.
        
        Args:
            user_id: UUID of the user
            file: FastAPI UploadFile containing the image
            session: SQLAlchemy AsyncSession for database operations
            
        Returns:
            dict: Response containing success message, user_id, and image_url
            
        Raises:
            HTTPException: For various error conditions
        """
        try:
            # Validate file type
            if not file.content_type.startswith('image/'):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid file type. Only images are allowed."
                )

            # Validate file size (max 5MB)
            max_size_bytes = 5 * 1024 * 1024
            if file.size > max_size_bytes:
                raise HTTPException(
                    status_code=400,
                    detail="File size exceeds 5MB limit."
                )

            # Get user from database
            user = await get_user(user_id=user_id, session=session)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            # Upload to S3 and get presigned URL
            image_url = await self.s3_service.upload_and_get_url(
                object_id=user_id,
                file=file,
                bucket_name=self.bucket_name,
                folder_prefix=self.folder_prefix,
                expiration=3600
            )

            # Update user in database
            user.profile_image_url = image_url
            await session.commit()
            await session.refresh(user)

            return {
                "message": "User image uploaded successfully",
                "user_id": str(user.id),
                "image_url": image_url
            }

        except HTTPException as he:
            raise he
        except Exception as e:
            logger.error(f"Failed to upload photograph: {str(e)}")
            await session.rollback()
            raise HTTPException(
                status_code=500,
                detail="Internal server error"
            )
        finally:
            await file.close()