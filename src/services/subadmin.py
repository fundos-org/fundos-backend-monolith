from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func
from sqlalchemy.orm import joinedload
from src.logging.logging_setup import get_logger
from src.models.subadmin import Subadmin
from src.models.deal import Deal, DealStatus
from src.models.user import User, KycStatus, Role
from src.models.investment import Investment, PaymentStatus
from uuid import UUID
from src.services.s3 import S3Service
from src.services.email import EmailService
from typing import Any
from datetime import datetime, timedelta
from sqlalchemy import and_

logger = get_logger(__name__)

class SubAdminService:
    def __init__(self):
        self.bucket_name = "fundos-dev-bucket"
        self.folder_prefix = "subadmin/profile_pictures/"
        self.s3_service = S3Service(bucket_name=self.bucket_name, region_name="ap-south-1")
        self.email_service = EmailService()

    async def subadmin_signin(
        self,
        session: AsyncSession,
        username: str,
        password: str
    ) -> Any:
        try:
            # Query Subadmin by username and password
            statement = select(Subadmin).where(
                and_(Subadmin.username == username, Subadmin.password == password)
            )
            result = await session.execute(statement)
            subadmin = result.scalar_one_or_none()

            if not subadmin:
                raise HTTPException(status_code=404, detail="Subadmin not found")

            return {
                "message": "User signed in successfully",
                "subadmin_id": str(subadmin.id),
                "name": subadmin.name,
                "username": subadmin.username,
                "password": subadmin.password,
                "invite_code": subadmin.invite_code,
                "success": True
            }
        except HTTPException as he:
            raise he
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to sign in subadmin: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to sign in subadmin: {str(e)}"
            )

    async def get_dashboard_statistics(
        self,
        session: AsyncSession,
        subadmin_id: UUID
    ) -> Any:
        try:
            # Fetch Subadmin
            subadmin = await session.get(Subadmin, subadmin_id)
            if not subadmin:
                raise HTTPException(status_code=404, detail="Subadmin not found")

            # Calculate total capital committed (sum of investments with completed payment status)
            investment_stmt = select(func.sum(Investment.amount)).join(Deal).where(
                and_(
                    Deal.fund_manager_id == subadmin_id,
                    Investment.payment_status == PaymentStatus.COMPLETED
                )
            )
            total_capital_committed = await session.execute(investment_stmt)
            total_capital_committed = total_capital_committed.scalar() or 0

            # Count listed startups (distinct companies in deals)
            listed_startups_stmt = select(func.count(func.distinct(Deal.company_name))).where(
                Deal.fund_manager_id == subadmin_id
            )
            listed_startups = await session.execute(listed_startups_stmt)
            listed_startups = listed_startups.scalar() or 0

            # Count onboarded investors (users with verified KYC)
            onboarded_investors_stmt = select(func.count(User.id)).where(
                and_(
                    User.fund_manager_id == subadmin_id,
                    User.kyc_status == KycStatus.VERIFIED
                )
            )
            onboarded_investors = await session.execute(onboarded_investors_stmt)
            onboarded_investors = onboarded_investors.scalar() or 0

            # Count deals this month
            current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            deals_this_month_stmt = select(func.count(Deal.id)).where(
                and_(
                    Deal.fund_manager_id == subadmin_id,
                    Deal.created_at >= current_month
                )
            )
            deals_this_month = await session.execute(deals_this_month_stmt)
            deals_this_month = deals_this_month.scalar() or 0

            result = {   
                        "subadmin_id": str(subadmin.id),
                        "subadmin_name" : subadmin.name or "",
                        "total_capital_committed": int(total_capital_committed),
                        "listed_startups": listed_startups,
                        "onboarded_investors": onboarded_investors,
                        "deals_this_month": deals_this_month
            }
            return result

        except HTTPException as he:
            raise he
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to fetch dashboard statistics: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch dashboard statistics: {str(e)}"
            )

    async def get_overview_graph(
        self,
        subadmin_id: UUID,
        session: AsyncSession
    ) -> Any:
        try:
            # Fetch Subadmin
            subadmin = await session.get(Subadmin, subadmin_id)
            if not subadmin:
                raise HTTPException(status_code=404, detail="Subadmin not found")

            # Get data for the last 30 days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            graph_data = []

            # Query investments and deals per day
            for day in range(30):
                day_start = start_date + timedelta(days=day)
                day_end = day_start + timedelta(days=1)

                # Sum investment amounts for the day
                investment_stmt = select(func.sum(Investment.amount)).join(Deal).where(
                    and_(
                        Deal.fund_manager_id == subadmin_id,
                        Investment.payment_status == PaymentStatus.COMPLETED,
                        Investment.created_at >= day_start,
                        Investment.created_at < day_end
                    )
                )
                amount = await session.execute(investment_stmt)
                amount = amount.scalar() or 0

                # Count deals created on the day
                deal_stmt = select(func.count(Deal.id)).where(
                    and_(
                        Deal.fund_manager_id == subadmin_id,
                        Deal.created_at >= day_start,
                        Deal.created_at < day_end
                    )
                )
                deal_count = await session.execute(deal_stmt)
                deal_count = deal_count.scalar() or 0

                graph_data.append({
                    "day_num": day + 1,
                    "amount": int(amount),
                    "deal_count": deal_count
                })

            return {
                "subadmin_id": str(subadmin.id),
                "subadmin_name": subadmin.name or "",
                "graph": graph_data
            }
        except HTTPException as he:
            raise he
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to fetch overview graph: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch overview graph: {str(e)}"
            )

    async def get_activities(
        self,
        session: AsyncSession,
        subadmin_id: UUID
    ) -> Any:
        try:
            # Fetch Subadmin
            subadmin = await session.get(Subadmin, subadmin_id)
            if not subadmin:
                raise HTTPException(status_code=404, detail="Subadmin not found")

            # Fetch recent investments (transactions) for the subadmin
            investment_stmt = select(Investment, User, Deal).join(User, Investment.investor_id == User.id).join(Deal, Investment.deal_id == Deal.id).where(
                and_(
                    Deal.fund_manager_id == subadmin_id,
                    Investment.payment_status == PaymentStatus.COMPLETED
                )
            ).order_by(Investment.created_at.desc()).limit(10)
            result = await session.execute(investment_stmt)
            investments = result.all()

            transactions = [
                {
                    "transaction_id": str(investment.Investment.id),
                    "investor": f"{investment.User.first_name} {investment.User.last_name or ''}".strip(),
                    "invested_in": investment.Deal.company_name or "Unknown",
                    "amount": str(investment.Investment.amount),
                    "transaction_date": investment.Investment.created_at.isoformat()
                }
                for investment in investments
            ]

            return {
                "subadmin_id": str(subadmin.id),
                "subadmin_name": subadmin.name or "",
                "transactions": transactions
            }
        except HTTPException as he:
            raise he
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to fetch activities: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch activities: {str(e)}"
            )

    async def get_transactions_details(
        self,
        session: AsyncSession,
        subadmin_id: UUID
    ) -> Any:
        try:
            # Fetch Subadmin
            subadmin = await session.get(Subadmin, subadmin_id)
            if not subadmin:
                raise HTTPException(status_code=404, detail="Subadmin not found")

            # Fetch all completed investments for the subadmin
            investment_stmt = select(Investment, User, Deal).join(User, Investment.investor_id == User.id).join(Deal, Investment.deal_id == Deal.id).where(
                and_(
                    Deal.fund_manager_id == subadmin_id,
                    Investment.payment_status == PaymentStatus.COMPLETED
                )
            ).order_by(Investment.created_at.desc())
            result = await session.execute(investment_stmt)
            investments = result.all()

            transactions = [
                {
                    "transaction_id": str(investment.Investment.id),
                    "investor": f"{investment.User.first_name} {investment.User.last_name or ''}".strip(),
                    "invested_in": investment.Deal.company_name or "Unknown",
                    "amount": investment.Investment.amount,
                    "transaction_date": investment.Investment.created_at.isoformat()
                }
                for investment in investments
            ]

            return {
                "subadmin_id": str(subadmin.id),
                "subadmin_name": subadmin.name or "",
                "transactions": transactions
            }
        except HTTPException as he:
            raise he
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to fetch transactions details: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch transactions details: {str(e)}"
            )

    async def get_deals_statistics(
        self,
        session: AsyncSession,
        subadmin_id: UUID
    ) -> Any:
        try:
            # Fetch Subadmin
            subadmin = await session.get(Subadmin, subadmin_id)
            if not subadmin:
                raise HTTPException(status_code=404, detail="Subadmin not found")

            # Count live deals (OPEN or ON_HOLD)
            live_deals_stmt = select(func.count(Deal.id)).where(
                and_(
                    Deal.fund_manager_id == subadmin_id,
                    Deal.status.in_([DealStatus.OPEN, DealStatus.ON_HOLD])
                )
            )
            live_deals = await session.execute(live_deals_stmt)
            live_deals = live_deals.scalar() or 0

            # Count closed deals
            closed_deals_stmt = select(func.count(Deal.id)).where(
                and_(
                    Deal.fund_manager_id == subadmin_id,
                    Deal.status == DealStatus.CLOSED
                )
            )
            closed_deals = await session.execute(closed_deals_stmt)
            closed_deals = closed_deals.scalar() or 0

            # Calculate total capital raised (sum of completed investments)
            total_capital_raised_stmt = select(func.sum(Investment.amount)).join(Deal).where(
                and_(
                    Deal.fund_manager_id == subadmin_id,
                    Investment.payment_status == PaymentStatus.COMPLETED
                )
            )
            total_capital_raised = await session.execute(total_capital_raised_stmt)
            total_capital_raised = total_capital_raised.scalar() or 0

            # Count deals this month
            current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            deals_this_month_stmt = select(func.count(Deal.id)).where(
                and_(
                    Deal.fund_manager_id == subadmin_id,
                    Deal.created_at >= current_month
                )
            )
            deals_this_month = await session.execute(deals_this_month_stmt)
            deals_this_month = deals_this_month.scalar() or 0

            return {
                "subadmin_id": str(subadmin.id),
                "subadmin_name": subadmin.name or "",
                "live_deals": live_deals,
                "closed_deals": closed_deals,
                "total_capital_raised": int(total_capital_raised),
                "deals_this_month": deals_this_month,
                "success":True
            }
        except HTTPException as he:
            raise he
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to fetch deals statistics: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch deals statistics: {str(e)}"
            )

    async def get_deals_overview(
        self,
        session: AsyncSession,
        subadmin_id: UUID
    ) -> Any:
        try:
            # Fetch Subadmin
            subadmin = await session.get(Subadmin, subadmin_id)
            if not subadmin:
                raise HTTPException(status_code=404, detail="Subadmin not found")

            # Fetch active deals (OPEN or ON_HOLD)
            active_deals_stmt = select(Deal).where(
                and_(
                    Deal.fund_manager_id == subadmin_id,
                    Deal.status.in_([DealStatus.OPEN, DealStatus.ON_HOLD])
                )
            )
            active_result = await session.execute(active_deals_stmt)
            active_deals = active_result.scalars().all()

            # Fetch closed deals
            closed_deals_stmt = select(Deal).where(
                and_(
                    Deal.fund_manager_id == subadmin_id,
                    Deal.status == DealStatus.CLOSED
                )
            )
            closed_result = await session.execute(closed_deals_stmt)
            closed_deals = closed_result.scalars().all()

            # Format deal data
            active_deals_list = [
                {
                    "deal_id": str(deal.id),
                    "company_name": deal.company_name or "Unknown",
                    "status": deal.status.value,
                    "round_size": deal.round_size or 0,
                    "created_at": deal.created_at.isoformat()
                }
                for deal in active_deals
            ]
            closed_deals_list = [
                {
                    "deal_id": str(deal.id),
                    "company_name": deal.company_name or "Unknown",
                    "status": deal.status.value,
                    "round_size": deal.round_size or 0,
                    "created_at": deal.created_at.isoformat()
                }
                for deal in closed_deals
            ]

            return {
                "subadmin_id": str(subadmin.id),
                "subadmin_name": subadmin.name or "",
                "active_deals": active_deals_list,
                "closed_deals": closed_deals_list, 
                "success":True
            }
        except HTTPException as he:
            raise he
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to fetch deals overview: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch deals overview: {str(e)}"
            )
        
    async def get_members_statistics(
        self,
        session: AsyncSession,
        subadmin_id: UUID
    ) -> Any:
        # fetch subadmin 
        subadmin = await session.get(Subadmin, subadmin_id)
        if not subadmin:
            raise HTTPException(status_code=404, detail="Subadmin not found")
        
        # fetch subadmin members (from user table fetch all the investors and startups onboarded by this subadmin(foreign key is fund_manager_id))
        investors_stmt = select(User).where(
            and_(
                User.fund_manager_id == subadmin_id,
                User.role == Role.INVESTOR
            )
        ).options(joinedload(User.investments))
        investors_result = await session.execute(investors_stmt)
        investors = investors_result.unique().scalars().all()

        investors_list = [
            {
                "user_id": str(investor.id),
                "first_name": investor.first_name or "",
                "last_name": investor.last_name or "",
                "email": investor.email or "",
                "capital_committed": investor.capital_commitment or 0,
                "kyc_status": investor.kyc_status
            } for investor in investors
        ] 

        startups_stmt = select(User).where(
            and_(
                User.fund_manager_id == subadmin_id,
                User.role == Role.FOUNDER
            )
        ).options(joinedload(User.investments))
        startups_result = await session.execute(startups_stmt)
        startups = startups_result.unique().scalars().all()

        # Fetch subadmin startups with the same filters as investors
        startups_list = [
            {
                "user_id": str(startup.id),
                "first_name": startup.first_name or "",
                "last_name": startup.last_name or "",
                "email": startup.email or "",
                "capital_committed": startup.capital_commitment or 0,
                "kyc_status": startup.kyc_status
            } for startup in startups
        ]

        subadmin_members = {
            "investors": investors_list,
            "startups": startups_list
        }

        investors_onboarded = len(investors)
        startups_onboarded = len(startups) 
        investors_kyc_pending = len([investor for investor in investors if investor.kyc_status == KycStatus.PENDING]) 
        startups_kyc_pending = len([startup for startup in startups if startup.kyc_status == KycStatus.PENDING]) 
        investors_started_investing = len([investor for investor in investors if len(investor.investments) > 0]) 
        startups_started_investing = len([startup for startup in startups if len(startup.investments) > 0]) 

        statistics = {
            "investors_statistics": {
                "onboarded": investors_onboarded or 0,
                "kyc_pending": investors_kyc_pending or 0,
                "started_investing": investors_started_investing or 0
            },
            "startups_statistics": {
                "onboarded": startups_onboarded or 0,
                "kyc_pending": startups_kyc_pending or 0,
                "started_investing": startups_started_investing or 0 
            }
        }

        return {
            "subadmin_id": str(subadmin.id),
            "subadmin_name": subadmin.name or "",
            "invite_code": subadmin.invite_code,
            "members": subadmin_members,
            "statistics": statistics,
            "success":True
        }
         
    async def add_members(
        self,
        session: AsyncSession,
        subadmin_id: UUID,
        email: str
    ) -> Any:
        try:
            # fetch subadmin 
            subadmin = await session.get(Subadmin, subadmin_id)
            if not subadmin:
                raise HTTPException(status_code=404, detail="Subadmin not found")
            
            # fetch user with email
            user = await session.get(User, email)
            if not user:
                # if not in team send the email to this user
                if await self.email_service.send_invitation_email(
                    email=email,
                    invite_code=subadmin.invite_code,
                    subadmin_name=subadmin.name or "",
                    user_name="",  # todo: fetch user name from db
                    apk_link="https://example.com/invite"
                )["success"]:
                    pass 
                else:
                    raise HTTPException(status_code=400, detail="Failed to send invitation email")
            
            # check if user is already a member of subadmin
            elif user.fund_manager_id == subadmin_id:
                raise HTTPException(status_code=400, detail="User is already a member of this subadmin")

            return {
                "user_id": str(user.id),
                "first_name": user.first_name or "",
                "last_name": user.last_name or "",
                "email": user.email or "",
                "role": user.role or "",
                "success": True
            }       
        except Exception as e:
            await session.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to add member: {str(e)}")
        