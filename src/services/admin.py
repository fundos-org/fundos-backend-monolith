from fastapi import HTTPException
from fastapi import UploadFile
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession
from src.logging.logging_setup import get_logger # assuming you have a logger setup
from pydantic import EmailStr
from src.models.user import User, investorType
from src.models.subadmin import Subadmin
from src.utils.dependencies import get_user
from uuid import UUID
from src.services.s3 import S3Service
from typing import Any
from datetime import datetime

logger = get_logger(__name__) 

class SubAdminService:
    def __init__(self):
        self.bucket_name = "fundos-dev-bucket"
        self.folder_prefix = "subadmin/profile_pictures/"
        self.s3_service = S3Service(bucket_name=self.bucket_name, region_name="ap-south-1")
  
    async def create_subadmin_profile(
            self, 
            session: AsyncSession, 
            name: str, 
            email: str, 
            contact: str, 
            about: str,
            logo: UploadFile, 
            ) -> Any:

        try: 
            # Validate file type
            if not logo.content_type.startswith('image/'):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid file type. Only images are allowed."
                )

            # Validate file size (max 5MB)
            max_size_bytes = 5 * 1024 * 1024
            if logo.size > max_size_bytes:
                raise HTTPException(
                    status_code=400,
                    detail="File size exceeds 5MB limit."
                )
            
            subadmin = Subadmin(
                name=name,
                email=email,
                contact=contact, 
                about=about
            )
            session.add(subadmin) 

            try: 
                # Upload to S3 and get presigned URL
                image_url = await self.s3_service.upload_and_get_url(
                    object_id=subadmin.id,
                    file=logo,
                    bucket_name=self.bucket_name,
                    folder_prefix=self.folder_prefix,
                    expiration=3600
                )
                subadmin = await session.get(User, subadmin.id) 
                
                # update the logo url 
                subadmin.logo = image_url 

            except Exception as e: 
                raise HTTPException(status_code=status.HTTP_417_EXPECTATION_FAILED, detail=f"failed to upload file to storage layer for subadmin: {subadmin.id} with error: {str(e)}" )
                
            
            await session.commit()
            await session.refresh(subadmin) 

            return {
                "success": True,
                "subadmin_id": subadmin.id
            }

        except Exception as e: 
            logger.error(f"Request failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Internal request error: {str(e)}")
     
    async def set_subadmin_credentials(
        self, 
        session: AsyncSession, 
        subadmin_id: UUID, 
        username: str, 
        password: str, 
        re_entered_password: str, 
        app_name: str, 
        invite_code: str
        ) -> Any: 

        try:
            subadmin = await session.get(Subadmin, subadmin_id)
            if not subadmin:
                raise HTTPException(status_code=404, detail="subadmin not found")

            subadmin.username = username
            subadmin.password = password
            subadmin.re_entered_password = re_entered_password
            subadmin.app_name = app_name
            subadmin.invite_code = invite_code
            
            subadmin.updated_at = datetime.now()

            await session.commit()
            await session.refresh(subadmin)

            return {
                "message": "details updated successfully", 
                "subadmin_obj": f"{subadmin}",
                "success": True
            }
        except HTTPException as he:
            raise he
        except Exception as e:
            logger.error(f"Failed to update subadmin credentials: {str(e)}")
            await session.rollback()
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
        
    async def get_subadmin_details(
        self, 
        subadmin_id: UUID, 
        session: AsyncSession
        ) -> Any:
        
        try:
            subadmin = await session.get(Subadmin, subadmin_id)

            if not subadmin:
                raise HTTPException(status_code=404, detail="subadmin not found")

            return {
                "message": "User details updated successfully",
                "subadmin_id": subadmin.id,
                "name": subadmin.name,
                "username": subadmin.username, 
                "password":subadmin.password, 
                "success": True
            }
        
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to fetch subadmin details: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to fetch subadmin details: {str(e)}")
        
    async def send_email_otp(self, email: EmailStr) -> dict:

        try:
            return {
                "message" : f"otp sent to: {email}", 
                "otp" : "123456" 
            }  

        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise HTTPException(status_code=500, detail="Internal request error")
        
    async def verify_email_otp(self, otp: str) -> dict: 

        try: 
            if otp == "123456" :
                return {
                    "message" : "otp code matched",
                    "success" : True
                }
            
        except Exception as e : 
            logger.error(f"Request failed: {e}")
            raise HTTPException(status_code=500, detail="Internal request error") 
        
    async def choose_investor_type(self, user_id: UUID, investor_type:investorType, session: AsyncSession) -> any :
        
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
        
    async def declaration_accepted( self, user_id: str, declaration_accepted: bool, session: AsyncSession) -> any : 

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
        
    async def set_professional_background( self, user_id: str, occupation: str, income_source: float, annual_income: float, capital_commitment: float, session: AsyncSession) -> any : 

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
        
    async def contribution_agreement(self, user_id: UUID, agreement_signed: bool, session: AsyncSession ) -> dict :

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
        
    async def upload_photograph(self, user_id: UUID, file: UploadFile, session: AsyncSession) -> dict:
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