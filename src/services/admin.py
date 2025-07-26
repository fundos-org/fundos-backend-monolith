from fastapi import HTTPException
from fastapi import UploadFile
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func
from src.logging.logging_setup import get_logger # assuming you have a logger setup
from src.models.subadmin import Subadmin
from src.models.user import User, Role
from src.models.deal import Deal, DealStatus
from src.schemas.admin import (
    SubadminDetails, SubadminListItem, SubadminDetailsResponse, SubadminDetailsUpdateResponse, AdminDashboardMetadataResponse, AdminOverviewPaginatedResponse, AdminOverviewItem, PaginationInfo
)
from uuid import UUID
from src.services.s3 import S3Service
from src.services.email import EmailService
from typing import Any
from datetime import datetime, timedelta
from src.configs.configs import aws_config, app_config
from sqlalchemy import cast, String


logger = get_logger(__name__) 

class AdminService:
    def __init__(self):
        self.bucket_name = aws_config.aws_bucket
        self.folder_prefix = aws_config.aws_subadmin_profile_pictures_folder
        
        # Initialize S3Service with error handling
        try:
            self.s3_service = S3Service(bucket_name=self.bucket_name, region_name="ap-south-1")
            self.s3_available = True
            logger.info("S3Service initialized successfully")
        except Exception as e:
            logger.warning(f"S3Service initialization failed: {str(e)}. Will use mock URLs for uploads.")
            self.s3_service = None
            self.s3_available = False
            
        self.email_service = EmailService()

    async def admin_signin(
        self, 
        session: AsyncSession, 
        username: str, 
        password: str
    ) -> Any:
        try:
            if username == "admin" and password == "Fundos":
                return {
                    "message": "User signed in successfully",
                    "success": True
                }
            else:
                return {
                    "message": "Invalid credentials",
                    "success": False
                }

        except Exception as e:
            logger.error(f"Failed to fetch subadmin details: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to fetch subadmin details: {str(e)}")
        except HTTPException as he:
            raise he
  
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
            # Provide temporary defaults for fields that will be set later via credentials API
            subadmin = Subadmin(
                name=name,
                email=email,
                contact=contact,
                about=about,
                username=f"temp_user_{datetime.now().strftime('%Y%m%d_%H%M%S')}",  # Temporary username
                password="TEMP_PASSWORD",  # Temporary password  
                re_entered_password="TEMP_PASSWORD",  # Temporary re-entered password
                app_name="TEMP_APP",  # Temporary app name
                invite_code=f"TEMP_CODE_{datetime.now().strftime('%Y%m%d_%H%M%S')}"  # Temporary invite code
            )

            # Add subadmin to the session
            session.add(subadmin)

            # Upload to S3 and get presigned URL, or use mock URL if S3 not available
            if self.s3_available:
                try:
                    image_url = await self.s3_service.upload_and_get_url(
                        object_id=subadmin.id,
                        file=logo,
                        bucket_name=self.bucket_name,
                        folder_prefix=self.folder_prefix,
                        expiration=3600,
                    )
                    subadmin.logo = image_url
                    logger.info(f"Successfully uploaded logo for subadmin: {subadmin.id}")
                except Exception as e:
                    # Log the S3 error but don't fail the entire operation
                    logger.warning(f"S3 upload failed for subadmin: {subadmin.id}, using mock URL. Error: {str(e)}")
                    # Use a mock/placeholder URL when S3 fails
                    mock_logo_url = f"https://ui-avatars.com/api/?name={name.replace(' ', '+')}&background=random&size=200"
                    subadmin.logo = mock_logo_url
            else:
                # S3 not available, use mock URL directly
                logger.info(f"S3 not available, using mock logo for subadmin: {subadmin.id}")
                mock_logo_url = f"https://ui-avatars.com/api/?name={name.replace(' ', '+')}&background=random&size=200"
                subadmin.logo = mock_logo_url

            # Commit the transaction
            await session.commit()
            await session.refresh(subadmin)

            # Check if we used a mock URL
            is_mock_logo = subadmin.logo.startswith("https://ui-avatars.com")
            
            if is_mock_logo:
                if not self.s3_available:
                    message = "Subadmin profile created successfully with mock logo (storage service unavailable)"
                else:
                    message = "Subadmin profile created successfully with mock logo (upload failed)"
            else:
                message = "Subadmin profile created successfully"

            return {
                "success": True,
                "subadmin_id": subadmin.id,
                "logo_url": subadmin.logo,
                "message": message
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

            # Check if invite_code is being changed and if there are existing users
            if subadmin.invite_code != invite_code:
                # Check if there are users with the current invite_code
                user_count_stmt = select(func.count(User.id)).where(
                    User.invitation_code == subadmin.invite_code
                )
                user_count_result = await session.execute(user_count_stmt)
                user_count = user_count_result.scalar() or 0
                
                if user_count > 0:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Cannot change invite_code. {user_count} users are currently using the existing invite_code '{subadmin.invite_code}'"
                    )

            subadmin.username = username
            subadmin.password = password
            subadmin.re_entered_password = re_entered_password
            subadmin.app_name = app_name
            subadmin.invite_code = invite_code
            
            subadmin.updated_at = datetime.now()

            await session.commit()
            await session.refresh(subadmin)

            return {
                "message": "Subadmin credentials updated successfully", 
                "subadmin_id": str(subadmin.id),
                "username": subadmin.username,
                "app_name": subadmin.app_name,
                "invite_code": subadmin.invite_code,
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
        session: AsyncSession,
        page: int = 1,
        per_page: int = 20
    ) -> Any:
        try:
            # Calculate offset for pagination
            offset = (page - 1) * per_page

            # Get total count
            count_query = select(func.count(Subadmin.id))
            total_count = await session.execute(count_query)
            total_records = total_count.scalar()

            # Get paginated subadmins
            query = select(Subadmin).offset(offset).limit(per_page)
            result = await session.execute(query)
            subadmins = result.scalars().all()

            # Calculate pagination info
            total_pages = (total_records + per_page - 1) // per_page
            has_next = page < total_pages
            has_prev = page > 1

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

            pagination_info = {
                "page": page,
                "per_page": per_page,
                "total_records": total_records,
                "total_pages": total_pages,
                "has_next": has_next,
                "has_prev": has_prev
            }

            return {
                "success": True,
                "subadmins": response,
                "pagination": pagination_info
            }
        except HTTPException as he:
            raise he
        except Exception as e:
            logger.error(f"Failed to fetch subadmin details: {str(e)}")
            await session.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to fetch subadmin details: {str(e)}")

    async def send_invitation(
        self,
        subadmin_id: UUID, 
        session: AsyncSession
    ) -> dict:
        try:
            subadmin = await session.get(Subadmin, subadmin_id)
            if not subadmin:
                raise HTTPException(status_code=404, detail="subadmin not found")

            if subadmin:
                # Do Sanity check & Send invitation email
                email_response = await self.email_service.send_invitation_to_subadmin(
                    email=subadmin.email,
                    invite_code=subadmin.invite_code,
                    user_name=subadmin.username or "",
                    password=subadmin.password or "",
                    apk_link=app_config.apk_link
                )

                is_email_sent = email_response.get("success", False)
                if not is_email_sent:
                    raise HTTPException(status_code=400, detail="Failed to send invitation email")

                # Return placeholder response for non-existing user
                return {
                    "message": f"Invitation email sent to {subadmin.email}",
                    "success": True
                }
            else:
                raise HTTPException(status_code=404, detail="subadmin not found")
            
        except HTTPException as he:
            logger.error(f"Failed to add member: {str(he)}")
            raise he
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to add member: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to add member: {str(e)}"
            )

    async def get_paginated_subadmins(
        self,
        session: AsyncSession,
        page: int = 1,
        per_page: int = 20
    ) -> dict:
        try:
            offset = (page - 1) * per_page
            count_query = select(func.count(Subadmin.id))
            total_count = await session.execute(count_query)
            total_records = total_count.scalar()
            query = select(Subadmin).offset(offset).limit(per_page)
            result = await session.execute(query)
            subadmins = result.scalars().all()
            total_pages = (total_records + per_page - 1) // per_page
            has_next = page < total_pages
            has_prev = page > 1
            subadmin_list = []
            for subadmin in subadmins:
                # Count total_users (investors with VERIFIED KYC under this subadmin)
                user_count_stmt = select(func.count(User.id)).where(
                    User.fund_manager_id == subadmin.id,
                    cast(User.role, String) == "INVESTOR",
                    cast(User.kyc_status, String) == "VERIFIED"
                )
                user_count_result = await session.execute(user_count_stmt)
                total_users = user_count_result.scalar() or 0
                # Count active deals (OPEN status under this subadmin)
                deal_count_stmt = select(func.count(Deal.id)).where(
                    Deal.fund_manager_id == subadmin.id,
                    cast(Deal.status, String) == "OPEN"
                )
                deal_count_result = await session.execute(deal_count_stmt)
                active_deals = deal_count_result.scalar() or 0
                subadmin_list.append(SubadminListItem(
                    subadmin_id=subadmin.id,
                    subadmin_name=subadmin.name or "",
                    email=subadmin.email or "",
                    invitation_code=subadmin.invite_code or "",
                    onboarding_date=subadmin.created_at.strftime("%Y-%m-%d"),
                    total_users=total_users,
                    active_deals=active_deals
                ))
            pagination_info = {
                "page": page,
                "per_page": per_page,
                "total_records": total_records,
                "total_pages": total_pages,
                "has_next": has_next,
                "has_prev": has_prev
            }
            return {
                "success": True,
                "subadmins": subadmin_list,
                "pagination": pagination_info
            }
        except Exception as e:
            logger.error(f"Failed to fetch paginated subadmins: {str(e)}")
            await session.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to fetch paginated subadmins: {str(e)}")

    async def get_subadmin_full_details(
        self,
        session: AsyncSession,
        subadmin_id: UUID
    ) -> dict:
        try:
            subadmin = await session.get(Subadmin, subadmin_id)
            if not subadmin:
                raise HTTPException(status_code=404, detail="Subadmin not found")
            # Use mock data for missing fields
            response = SubadminDetailsResponse(
                subadmin_id=subadmin.id,
                logo=subadmin.logo or "https://mock.logo.url/logo.png",
                name=subadmin.name or "",
                email=subadmin.email or "",
                contact=subadmin.contact or "",
                about=subadmin.about or "",
                username=subadmin.username or "",
                password=subadmin.password or "",
                reenter_password=subadmin.re_entered_password or "",
                app_name=subadmin.app_name or "FundosApp",
                invite_code=subadmin.invite_code or "",
                app_theme="light",  # mock data
                success=True
            )
            return response.dict()
        except Exception as e:
            logger.error(f"Failed to fetch subadmin details: {str(e)}")
            await session.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to fetch subadmin details: {str(e)}")

    async def update_subadmin_full_details(
        self,
        session: AsyncSession,
        subadmin_id: UUID,
        update_data: dict
    ) -> dict:
        try:
            subadmin = await session.get(Subadmin, subadmin_id)
            if not subadmin:
                raise HTTPException(status_code=404, detail="Subadmin not found")
            # Update fields if present in update_data
            for field in ["logo", "name", "email", "contact", "about", "username", "password", "re_entered_password", "app_name", "invite_code"]:
                if field in update_data and update_data[field] is not None:
                    setattr(subadmin, field if field != "re_entered_password" else "re_entered_password", update_data[field])
            subadmin.updated_at = datetime.now()
            await session.commit()
            return SubadminDetailsUpdateResponse(
                subadmin_id=subadmin.id,
                message="Subadmin details updated successfully",
                success=True
            ).dict()
        except Exception as e:
            logger.error(f"Failed to update subadmin details: {str(e)}")
            await session.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to update subadmin details: {str(e)}")

    async def get_admin_dashboard_metadata(
        self,
        session: AsyncSession
    ) -> dict:
        """
        Get admin dashboard metadata including total subadmins, users, active deals, and new users this month.
        
        Returns:
            dict: Dashboard metadata containing counts for various entities
        """
        try:
            # Count total subadmins from subadmin table
            total_admin_stmt = select(func.count(Subadmin.id))
            total_admin_result = await session.execute(total_admin_stmt)
            total_admin_onboarded = total_admin_result.scalar() or 0

            # Count total users where role is INVESTOR
            total_users_stmt = select(func.count(User.id)).where(
                cast(User.role, String) == "INVESTOR"
            )
            total_users_result = await session.execute(total_users_stmt)
            total_users = total_users_result.scalar() or 0

            # Count active deals (OPEN status)
            active_deals_stmt = select(func.count(Deal.id)).where(
                cast(Deal.status, String) == "OPEN"
            )
            active_deals_result = await session.execute(active_deals_stmt)
            active_deals = active_deals_result.scalar() or 0

            # Count new users this month (users with role INVESTOR created within last 30 days)
            one_month_ago = datetime.now().replace(tzinfo=None) - timedelta(days=30)
            new_users_stmt = select(func.count(User.id)).where(
                cast(User.role, String) == "INVESTOR",
                User.created_at >= one_month_ago
            )
            new_users_result = await session.execute(new_users_stmt)
            new_user_this_month = new_users_result.scalar() or 0

            logger.info(f"Admin dashboard metadata retrieved: {total_admin_onboarded} admins, {total_users} users, {active_deals} active deals, {new_user_this_month} new users this month")

            return AdminDashboardMetadataResponse(
                total_admin_onboarded=total_admin_onboarded,
                total_users=total_users,
                active_deals=active_deals,
                new_user_this_month=new_user_this_month,
                success=True
            ).dict()

        except Exception as e:
            logger.error(f"Failed to fetch admin dashboard metadata: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch admin dashboard metadata: {str(e)}"
            )

    async def get_admin_overview_paginated(
        self,
        session: AsyncSession,
        page: int = 1,
        per_page: int = 10
    ) -> dict:
        """
        Get paginated admin overview including subadmin details with their associated user and deal counts.
        
        Args:
            session: Database session
            page: Page number (default: 1)
            per_page: Items per page (default: 10)
            
        Returns:
            dict: Paginated admin overview with counts for users and deals under each subadmin
        """
        try:
            # Calculate offset for pagination
            offset = (page - 1) * per_page

            # Get total count of subadmins for pagination
            total_count_stmt = select(func.count(Subadmin.id))
            total_count_result = await session.execute(total_count_stmt)
            total_records = total_count_result.scalar() or 0

            # Calculate total pages
            total_pages = (total_records + per_page - 1) // per_page

            # Get paginated subadmins
            subadmins_stmt = select(Subadmin).offset(offset).limit(per_page).order_by(Subadmin.created_at.desc())
            subadmins_result = await session.execute(subadmins_stmt)
            subadmins = subadmins_result.scalars().all()

            # Build admin overview list
            admin_overview_list = []
            for subadmin in subadmins:
                # Count total users (INVESTOR role) under this subadmin
                total_users_stmt = select(func.count(User.id)).where(
                    User.fund_manager_id == subadmin.id,
                    cast(User.role, String) == "INVESTOR"
                )
                total_users_result = await session.execute(total_users_stmt)
                total_users = total_users_result.scalar() or 0

                # Count active deals (OPEN status) under this subadmin
                active_deals_stmt = select(func.count(Deal.id)).where(
                    Deal.fund_manager_id == subadmin.id,
                    cast(Deal.status, String) == "OPEN"
                )
                active_deals_result = await session.execute(active_deals_stmt)
                active_deals = active_deals_result.scalar() or 0

                # Format onboarding date
                onboarding_date = subadmin.created_at.strftime("%Y-%m-%d") if subadmin.created_at else ""

                admin_overview_item = AdminOverviewItem(
                    admin_id=str(subadmin.id),
                    admin_name=subadmin.name or "",
                    email=subadmin.email or "",
                    invitation_code=subadmin.invite_code or "",
                    total_users=total_users,
                    active_deals=active_deals,
                    onboarding_date=onboarding_date
                )
                admin_overview_list.append(admin_overview_item)

            # Create pagination info
            pagination_info = PaginationInfo(
                page=page,
                per_page=per_page,
                total_records=total_records,
                total_pages=total_pages,
                has_next=page < total_pages,
                has_prev=page > 1
            )

            logger.info(f"Admin overview paginated retrieved: page {page}, {len(admin_overview_list)} admins, total {total_records} records")

            return AdminOverviewPaginatedResponse(
                admins=admin_overview_list,
                pagination=pagination_info,
                success=True
            ).dict()

        except Exception as e:
            logger.error(f"Failed to fetch admin overview paginated: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch admin overview paginated: {str(e)}"
            )