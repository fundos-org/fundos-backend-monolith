from fastapi import HTTPException
from fastapi import UploadFile
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from src.logging.logging_setup import get_logger # assuming you have a logger setup
from src.models.subadmin import Subadmin
from src.schemas.admin import SubadminDetails
from uuid import UUID
from src.services.s3 import S3Service
from typing import Any
from datetime import datetime


logger = get_logger(__name__) 

class AdminService:
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
            if not logo.content_type.startswith("image/"):
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

            # Create Subadmin instance with all required fields
            subadmin = Subadmin(
                name=name,
                email=email,
                contact=contact,
                about=about
            )

            # Add subadmin to the session
            session.add(subadmin)

            # Upload to S3 and get presigned URL
            try:
                image_url = await self.s3_service.upload_and_get_url(
                    object_id=subadmin.id,
                    file=logo,
                    bucket_name=self.bucket_name,
                    folder_prefix=self.folder_prefix,
                    expiration=3600,
                )
                subadmin.logo = image_url
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_417_EXPECTATION_FAILED,
                    detail=f"Failed to upload file to storage layer for subadmin: {subadmin.id} with error: {str(e)}",
                )

            # Commit the transaction
            await session.commit()
            await session.refresh(subadmin)

            return {
                "success": True,
                "subadmin_id": subadmin.id,
            }

        except HTTPException as he:
            raise he
        except Exception as e:
            logger.error(f"Request failed: {str(e)}")
            await session.rollback()
            raise HTTPException(status_code=500, detail=f"Internal request error: {str(e)}")
        finally:
            await logo.close()
     
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
                "subadmin_id": subadmin.id,
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
                "invite_code": subadmin.invite_code,
                "success": True
            }
        
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to fetch subadmin details: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to fetch subadmin details: {str(e)}")
        
        except HTTPException as he:
            raise he 
        
    async def get_all_subadmins(
        self, 
        session: AsyncSession
    ) -> Any:
        try:
            # Query all Subadmin records
            result = await session.execute(select(Subadmin))
            subadmins = result.scalars().all()

            # Prepare response data
            response = []
            for subadmin in subadmins:

                # Placeholder for total_users and active_deals (to be computed)
                total_users = 0  # Replace with actual logic (e.g., count related users)
                active_deals = 0  # Replace with actual logic (e.g., count active deals)

                response.append(SubadminDetails(
                    subadmin_id=subadmin.id,
                    name=subadmin.name,
                    email=subadmin.email,
                    invite_code=subadmin.invite_code or "",  # Handle null invite_code
                    total_users=total_users,
                    active_deals=active_deals,
                    onboarding_date=subadmin.created_at.strftime("%d/%m/%Y")
                ))

            return {
                "success":True,
                "subadmins": response
            }
        except HTTPException as he:
            raise he
        except Exception as e:
            logger.error(f"Failed to fetch subadmin details: {str(e)}")
            await session.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to fetch subadmin details: {str(e)}")