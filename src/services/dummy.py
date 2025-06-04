from fastapi import HTTPException
from fastapi import UploadFile
from sqlalchemy import and_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from src.models.kyc import KYC
from src.services.phone import PhoneService
from src.logging.logging_setup import get_logger # assuming you have a logger setup
from pydantic import EmailStr
from src.models.user import User, investorType, OnboardingStatus
from src.models.subadmin import Subadmin
from src.utils.dependencies import get_user
from uuid import UUID
from src.services.s3 import S3Service
from src.services.email import EmailService
from typing import Dict, Any, Optional

logger = get_logger(__name__) 

class DummyService:
    def __init__(self):
        self.bucket_name = "fundos-dev-bucket"
        self.folder_prefix = "users/profile_pictures/"
        self.s3_service = S3Service(bucket_name=self.bucket_name, region_name="ap-south-1")
        self.email_service = EmailService()
        self.phone_service = PhoneService()
    
    async def investor_signin_email(
        self, 
        session: AsyncSession, 
        email: EmailStr
    ) -> Any:
        try:
            # Fetch user from the database
            stmt = select(User).where(
                User.email == email
            )

            result = await session.execute(stmt)
            user = result.scalar_one_or_none() 

            if user:
                response =await self.email_service.send_email_otp(
                    email=email, 
                    subject = "OTP Code for Sign to Fundos"
                )
                if response.get("success"): 
                    return {
                        "message": f"An otp send to {email} for verification",
                        "success": True
                    }
            else:
                return {
                    "message": "User not found in fundos",
                    "success": False
                }

        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise HTTPException(status_code=500, detail=f"Internal request error : {str(e)}")
    
    async def investor_signin_email_verify(
        self, 
        session: AsyncSession,
        email: EmailStr,
        otp_code: str
    )-> Any:
        try: 
            # Verify the OTP
            response = await self.email_service.verify_email_otp(
                email=email,
                otp_code=otp_code    
            )

            if response.get("success"):
                # Fetch user from the database
                stmt = select(User).where(
                    User.email == email
                )

                result = await session.execute(stmt)
                user = result.scalar_one_or_none() 

                if user:
                    return {
                        "message": f"User {user.first_name} signed in successfully",
                        "user_name": str(user.first_name) + " " + str(user.last_name),
                        "fund_manager_id": str(user.fund_manager_id),
                        "success": True
                    }
                else:
                    return {
                        "message": "User not found in fundos",
                        "user_id": None,
                        "fund_manager_id": None,
                        "success": False
                    }
            else:
                return {
                    "message": "Invalid OTP",
                    "success": False
                }
        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise HTTPException(status_code=500, detail=f"Internal request error : {str(e)}")

    async def send_phone_otp(
        self, 
        session: AsyncSession,
        phone_number: str,
        invite_code: Optional[str] = None
    ) -> Dict[str, Any]:
        try:
            # Check if user already exists in the database
            stmt = select(User).where(User.phone_number == phone_number)
            result = await session.execute(stmt)
            user = result.scalars().first()

            if user:
                # Repeated flow: User exists
                result = await self.phone_service.send_phone_otp(
                    phone_number=phone_number,
                    user_name=user.full_name or "Investor",
                    country="india", 
                    process="signin"
                )
                if not result["success"]:
                    return {
                        "message": f"Failed to send OTP to {phone_number}", 
                        "success": False
                    }
                return {
                    "user_id": user.id,
                    "subadmin_id": user.fund_manager_id,
                    "onboarding_status": user.onboarding_status,
                    "message": "OTP sent successfully",
                    "success": True
                }
            else:
                # First-time user flow
                if not invite_code:
                    # If invite code is not provided, indicate it’s needed
                    return {
                        "need_invite_code": True,
                        "message": "Invite code required for new user",
                        "success": False
                    }

                # Validate invite code by checking the Subadmin table
                stmt = select(Subadmin).where(Subadmin.invite_code == invite_code)
                result = await session.execute(stmt)
                subadmin = result.scalar_one_or_none()

                if not subadmin:
                    return {
                        "message": "Invalid invite code",
                        "success": False
                    }

                # Send OTP for signup
                result = await self.phone_service.send_phone_otp(
                    phone_number=phone_number,
                    user_name="Investor",
                    country="india", 
                    process="signup"
                )
                if not result["success"]:
                    return {
                        "message": f"Failed to send OTP to {phone_number}", 
                        "success": False
                    }
                return {
                    "message": "OTP sent successfully for signup",
                    "success": True
                }

        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise HTTPException(status_code=500, detail=f"Internal request error: {str(e)}")

    async def verify_phone_otp(
        self, 
        otp_code: str, 
        phone_number: str, 
        session: AsyncSession,
        invite_code: Optional[str] = None, 
    ) -> Dict[str, Any]:
        try:
            # Verify the OTP
            result = await self.phone_service.verify_phone_otp(
                phone_number=phone_number,
                otp=otp_code, 
                country="india"
            )
            if not result["success"]:
                return {
                    "message": "OTP verification failed",
                    "success": False
                }

            # Check if user exists
            stmt = select(User).where(User.phone_number == phone_number)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            if user:
                # Repeated flow: Existing user (login)
                return {
                    "user_id": user.id,
                    "subadmin_id": user.fund_manager_id,
                    "onboarding_status": user.onboarding_status,
                    "message": "OTP verified successfully",
                    "success": True
                }
            else:
                # First-time user flow: Create new user
                if not invite_code:
                    return {
                        "message": "Invite code required for new user",
                        "success": False
                    }

                # Validate invite code
                stmt = select(Subadmin).where(Subadmin.invite_code == invite_code)
                result = await session.execute(stmt)
                subadmin = result.scalar_one_or_none()

                if not subadmin:
                    return {
                        "message": "Invalid invite code",
                        "success": False
                    }

                # Create new user
                user = User(
                    invitation_code=invite_code,
                    onboarding_status=OnboardingStatus.Invitation_Code_Verified.name,
                    phone_number=phone_number,
                    fund_manager_id=subadmin.id
                )
                session.add(user)
                await session.commit()
                await session.refresh(user)

                return {
                    "user_id": user.id,
                    "subadmin_id": subadmin.id,
                    "onboarding_status": user.onboarding_status,
                    "message": "User created and OTP verified successfully",
                    "success": True
                }

        except HTTPException as he:
            raise he
        except Exception as e:
            logger.error(f"Failed to verify OTP: {str(e)}")
            await session.rollback()
            raise HTTPException(status_code=500, detail="Internal server error")
       
    async def verify_invitation_code(
        self, 
        invitation_code: str,
        phone_number: str,
        session: AsyncSession    
    ) -> Dict[str, Any]:

        try:

            # Validate phone number: must be exactly the expected length and digits only
            if not phone_number.isdigit():
                raise HTTPException(status_code=400, detail="Phone number must contain only digits")
            if len(phone_number) != 10:
                raise HTTPException(status_code=400, detail=f"Phone number must be 10 digits")

            # Check if invitation code exists in Subadmin table
            stmt = select(Subadmin).where(Subadmin.invite_code == invitation_code)
            result = await session.execute(stmt)
            subadmin = result.scalar_one_or_none()

            if subadmin:
                # Create new user with the valid invitation code
                user = User(
                    invitation_code=invitation_code,
                    onboarding_status=OnboardingStatus.Invitation_Code_Verified.name,
                    phone_number=phone_number,
                    fund_manager_id=subadmin.id  # Link user to subadmin
                )
                session.add(user)
                await session.commit()
                await session.refresh(user)

                return {
                    "success": True,
                    "message": "User created successfully",
                    "user_id": user.id,
                    "fund_manager_id": subadmin.id
                }
            else:
                return {
                    "success": False,
                    "message": "Error: Invalid invitation code"
                }

        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise HTTPException(status_code=500, detail="Internal request error")
       
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
    ) -> Dict[str, Any]:

        try:
            # Send OTP to the email
            response = await self.email_service.send_email_otp(
                email=email,
                subject="OTP Code for Fundos",
            ) 

            if response.get("success"):
                return {
                    "message": f"OTP sent to: {email}",
                    "success": True
                } 
            else: 
                return {
                    "message": "Failed to send OTP",
                    "success": False
                }

        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise HTTPException(status_code=500, detail="Internal request error")
        
    async def verify_email_otp(
        self, 
        user_id: UUID, 
        session: AsyncSession,
        otp: str, 
        email: EmailStr
    ) -> Dict[str, Any]: 

        try: 
            # Verify the OTP
            response = await self.email_service.verify_email_otp(
                email=email,
                otp_code=otp    
            )

            if response.get("success"):
                # Fetch user from the database
                user = await session.get(User, user_id)
                user.email = email 
                user.onboarding_status = OnboardingStatus.Email_Verified

                await session.commit()
                await session.refresh(user)

                return {
                    "message": f"email verified for user: {user_id}",
                    "success": True
                }
                
            else: 
                return {
                    "message": "Invalid OTP",
                    "success": False
                }
            
        except Exception as e : 
            await session.rollback()
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
            user.onboarding_status = OnboardingStatus.Zoho_Document_Sent.name

            await session.commit()
            await session.refresh(user) 

            return {
                "message": "User signed agreement ",
                "user_id": user_id,
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
            user.onboarding_status = OnboardingStatus.Completed.name
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

    async def delete_user_record(
        self, 
        phone_number: str, 
        invitation_code: str,
        session: AsyncSession,
    ) -> Dict[str, Any]:
        try:
            statement = select(User).where(
                and_(
                    User.phone_number == phone_number,
                    User.invitation_code == invitation_code
                )
            )
            result = await session.execute(statement)
            user = result.scalars().first()

            if user:
                stmt = select(KYC).where(KYC.user_id == user.id)
                result = await session.execute(stmt)
                kyc = result.scalars().first()

                if kyc:
                    await session.delete(kyc)
                    await session.commit()

                await session.delete(user)
                await session.commit()

                response = {
                    "message": "User record deleted successfully",
                    "success": True
                }
            else:
                response = {
                    "message": "User not found",
                    "success": False
                }
                
            return response
                
        except Exception as e:
            logger.error(f"Failed to delete user record: {str(e)}")
            await session.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to delete user record: {str(e)}")
            
    async def delete_all_users(
        self, 
        session: AsyncSession
    ) -> Dict[str, Any]:
        try:
            # Step 1: Delete all rows from the KYC table to avoid foreign key constraints
            kyc_stmt = delete(KYC)
            kyc_result = await session.execute(kyc_stmt)
            logger.info(f"Deleted {kyc_result.rowcount} rows from KYC table")

            # Step 2: Delete all rows from the User table
            user_stmt = delete(User)
            user_result = await session.execute(user_stmt)
            logger.info(f"Deleted {user_result.rowcount} rows from User table")

            # Commit the transaction
            await session.commit()

            return {
                "message": "All users and related KYC data deleted successfully",
                "success": True,
                "users_deleted": user_result.rowcount,
                "kyc_deleted": kyc_result.rowcount
            }

        except Exception as e:
            logger.error(f"Failed to delete users: {str(e)}")
            await session.rollback()
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")        