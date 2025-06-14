from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func
from sqlalchemy.orm import joinedload
from src.logging.logging_setup import get_logger
from src.models.subadmin import Subadmin
from src.models.deal import Deal, DealStatus
from src.models.user import User, KycStatus, Role
from src.models.investment import Investment
from src.models.transaction import Transaction, TransactionStatus, TransactionType
from src.services.s3 import S3Service
from src.services.email import EmailService
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy import and_ 
from src.configs.configs import aws_config

# sample data for frontend 
from src.utils.dummy_data import (
    activities_data,
    transaction_data
)
logger = get_logger(__name__)

class SubAdminService:
    def __init__(self):
        self.bucket_name = aws_config.aws_bucket
        self.folder_prefix = aws_config.aws_subadmin_profile_pictures_folder
        self.s3_service = S3Service(bucket_name=self.bucket_name, region_name="ap-south-1")
        self.email_service = EmailService()

    async def subadmin_signin(
        self,
        session: AsyncSession,
        username: str,
        password: str
    ) -> dict:
        try:
            # Query Subadmin by username and password
            statement = select(Subadmin).where(
                and_(Subadmin.username == username, Subadmin.password == password)
            )
            result = await session.execute(statement)
            subadmin = result.scalar_one_or_none()

            if not subadmin:
                # Raise 404 if subadmin not found
                raise HTTPException(status_code=404, detail="Subadmin not found")

            return {
                "message": "User signed in successfully",
                "subadmin_id": str(subadmin.id),
                "name": subadmin.name,
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
    ) -> dict:
        try:
            # Fetch Subadmin
            subadmin = await session.get(Subadmin, subadmin_id)
            if not subadmin:
                raise HTTPException(status_code=404, detail="Subadmin not found")

            # Calculate total capital committed (sum of Investment.amount where Transaction is COMPLETED)
            capital_committed_stmt = select(func.sum(User.capital_commitment)).where(
                and_(
                    User.fund_manager_id == subadmin_id
                )
            )
            total_capital_committed = await session.execute(capital_committed_stmt)
            total_capital_committed = total_capital_committed.scalar() or 0

            # Count listed startups (distinct companies in deals)
            listed_startups_stmt = select(func.count(User.id)).where(
                and_(
                    User.fund_manager_id == subadmin_id,
                    User.role == Role.FOUNDER
                )
            )
            listed_startups = await session.execute(listed_startups_stmt)
            listed_startups = listed_startups.scalar() or 0

            # Count onboarded investors (users with verified KYC)
            onboarded_investors_stmt = select(func.count(User.id)).where(
                and_(
                    User.fund_manager_id == subadmin_id,
                    User.role == Role.INVESTOR
                )
            )
            onboarded_investors = await session.execute(onboarded_investors_stmt)
            onboarded_investors = onboarded_investors.scalar() or 0

            # Count deals this month (use naive datetime to match TIMESTAMP WITHOUT TIME ZONE)
            current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
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
                "total_capital_committed": int(total_capital_committed),
                "listed_startups": listed_startups,
                "onboarded_investors": onboarded_investors,
                "deals_this_month": deals_this_month,
                "success": True
            }
        except HTTPException as he:
            raise he
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to fetch dashboard statistics: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch dashboard statistics: {str(e)}"
            )

    async def get_overview_graph(
        self,
        subadmin_id: UUID,
        session: AsyncSession
    ) -> dict:
        try:
            # Fetch Subadmin
            subadmin = await session.get(Subadmin, subadmin_id)
            if not subadmin:
                raise HTTPException(status_code=404, detail="Subadmin not found")

            # Get data for the last 30 days (use naive datetimes)
            end_date = datetime.now().replace(tzinfo=None)
            start_date = end_date - timedelta(days=30)
            graph_data = []

            # Query investments and deals per day
            for day in range(30):
                day_start = start_date + timedelta(days=day)
                day_end = day_start + timedelta(days=1)

                # Sum investment amounts for the day
                investment_stmt = select(func.sum(Investment.amount)).join(Deal).join(
                    Transaction, Transaction.investment_id == Investment.id
                ).where(
                    and_(
                        Deal.fund_manager_id == subadmin_id,
                        Transaction.status == TransactionStatus.COMPLETED,
                        Transaction.transaction_type == TransactionType.PAYMENT,
                        Transaction.created_at >= day_start,
                        Transaction.created_at < day_end
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
                "graph": graph_data,
                "success": True
            }
        except HTTPException as he:
            raise he
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to fetch overview graph: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch overview graph: {str(e)}"
            )

    async def get_activities(
        self,
        session: AsyncSession,
        subadmin_id: UUID
    ) -> dict:
        try:
            return activities_data
            # Fetch Subadmin
            subadmin = await session.get(Subadmin, subadmin_id)
            if not subadmin:
                raise HTTPException(status_code=404, detail="Subadmin not found")

            # Fetch recent transactions for the subadmin
            transaction_stmt = select(Transaction, Investment, User, Deal).join(
                Investment, Transaction.investment_id == Investment.id
            ).join(
                User, Investment.investor_id == User.id
            ).join(
                Deal, Investment.deal_id == Deal.id
            ).where(
                and_(
                    Deal.fund_manager_id == subadmin_id,
                    Transaction.status == TransactionStatus.COMPLETED,
                    Transaction.transaction_type == TransactionType.PAYMENT
                )
            ).order_by(Transaction.created_at.desc()).limit(10)
            result = await session.execute(transaction_stmt)
            transactions = result.all()

            transaction_details = [
                {
                    "transaction_id": str(transaction.Transaction.id),
                    "investor": f"{transaction.User.first_name} {transaction.User.last_name or ''}".strip(),
                    "invested_in": transaction.Deal.company_name or "Unknown",
                    "amount": float(transaction.Investment.amount),
                    "transaction_date": transaction.Transaction.created_at.isoformat()
                }
                for transaction in transactions
            ]

            return {
                "subadmin_id": str(subadmin.id),
                "subadmin_name": subadmin.name or "",
                "transactions": transaction_details,
                "success": True
            }
        except HTTPException as he:
            raise he
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to fetch activities: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch activities: {str(e)}"
            )

    async def get_transactions_details(
        self,
        session: AsyncSession,
        subadmin_id: UUID
    ) -> dict:
        try:
            return transaction_data
            # Fetch Subadmin
            subadmin = await session.get(Subadmin, subadmin_id)
            if not subadmin:
                raise HTTPException(status_code=404, detail="Subadmin not found")

            # Fetch all completed transactions for the subadmin
            transaction_stmt = select(Transaction, Investment, User, Deal).join(
                Investment, Transaction.investment_id == Investment.id
            ).join(
                User, Investment.investor_id == User.id
            ).join(
                Deal, Investment.deal_id == Deal.id
            ).where(
                and_(
                    Deal.fund_manager_id == subadmin_id,
                    Transaction.status == TransactionStatus.COMPLETED,
                    Transaction.transaction_type == TransactionType.PAYMENT
                )
            ).order_by(Transaction.created_at.desc())
            result = await session.execute(transaction_stmt)
            transactions = result.all()

            transaction_activities = [
                {
                    "transaction_id": str(transaction.Transaction.id),
                    "investor": f"{transaction.User.first_name} {transaction.User.last_name or ''}".strip(),
                    "invested_in": transaction.Deal.company_name or "Unknown",
                    "amount": float(transaction.Investment.amount),
                    "transaction_date": transaction.Transaction.created_at.isoformat()
                }
                for transaction in transactions
            ]

            # Fetch all investors who joined using this subadmin
            investor_joined_stmt = select(User).where(
                and_(
                    User.invitation_code == subadmin.invite_code,
                    User.role == Role.INVESTOR
                )
            ).order_by(User.created_at.desc())
            result = await session.execute(investor_joined_stmt)
            investors_joined = result.scalars().all()

            onboarding_activities = [
                {
                    "investor_id": str(investor.id),
                    "investor_name": f"{investor.first_name} {investor.last_name or ''}".strip(),
                    "joined_date": investor.created_at.isoformat()
                }
                for investor in investors_joined
            ]

            # Fetch all investors who completed KYC
            investor_kyc_stmt = select(User).where(
                and_(
                    User.invitation_code == subadmin.invite_code,
                    User.role == Role.INVESTOR,
                    User.kyc_status == KycStatus.VERIFIED
                )
            ).order_by(User.updated_at.desc())
            result = await session.execute(investor_kyc_stmt)
            investors_kyc = result.scalars().all()

            investor_kyc_activities = [
                {
                    "investor_id": str(investor.id),
                    "investor_name": f"{investor.first_name} {investor.last_name or ''}".strip(),
                    "kyc_completed_date": investor.updated_at.isoformat()
                }
                for investor in investors_kyc
            ]

            return {
                "subadmin_id": str(subadmin.id),
                "subadmin_name": subadmin.name or "",
                "transaction_activities": transaction_activities,
                "onboarding_activities": onboarding_activities,
                "investor_kyc_activities": investor_kyc_activities,
                "success": True
            }
        except HTTPException as he:
            raise he
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to fetch transactions details: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch transactions details: {str(e)}"
            )

    async def get_deals_statistics(
        self,
        session: AsyncSession,
        subadmin_id: UUID
    ) -> dict:
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

            # Calculate total capital raised (sum of Investment.amount where Transaction is COMPLETED)
            total_capital_raised_stmt = select(func.sum(Investment.amount)).join(Deal).join(
                Transaction, Transaction.investment_id == Investment.id
            ).where(
                and_(
                    Deal.fund_manager_id == subadmin_id,
                    Transaction.status == TransactionStatus.COMPLETED,
                    Transaction.transaction_type == TransactionType.PAYMENT
                )
            )
            total_capital_raised = await session.execute(total_capital_raised_stmt)
            total_capital_raised = total_capital_raised.scalar() or 0

            # Count deals this month (use naive datetime to match TIMESTAMP WITHOUT TIME ZONE)
            current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
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
                "success": True
            }
        except HTTPException as he:
            raise he
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to fetch deals statistics: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch deals statistics: {str(e)}"
            )

    async def get_deals_overview(
        self,
        session: AsyncSession,
        subadmin_id: UUID
    ) -> dict:
        try:
            # Fetch Subadmin
            subadmin = await session.get(Subadmin, subadmin_id)
            if not subadmin:
                raise HTTPException(status_code=404, detail="Subadmin not found")

            # Fetch active deals (OPEN or ON_HOLD)
            active_deals_stmt = select(Deal).where(
                and_(
                    Deal.fund_manager_id == subadmin_id,
                    Deal.status == DealStatus.OPEN
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

            onhold_deals_stmt = select(Deal).where(
                and_(
                    Deal.fund_manager_id == subadmin_id,
                    Deal.status == DealStatus.ON_HOLD
                )
            )
            onhold_result = await session.execute(onhold_deals_stmt)
            onhold_deals = onhold_result.scalars().all()

            # Format deal data
            active_deals_list = [
                {
                    "deal_id": str(deal.id),
                    "description": deal.about_company,
                    "title": deal.company_name,
                    "deal_status": deal.status,
                    "current_valuation": deal.current_valuation,
                    "round_size": deal.round_size,
                    "commitment": deal.syndicate_commitment,
                    "business_model": deal.business_model,
                    "company_stage": deal.company_stage,
                    "minimum_investment": deal.minimum_investment, 
                    "instruments": deal.instrument_type, 
                    "fund_raised_till_now": 0 ,
                    "logo_url": deal.logo_url,
                    "created_at": deal.created_at, 
                }
                for deal in active_deals
            ]
            closed_deals_list = [
                {
                    "deal_id": str(deal.id),
                    "description": deal.about_company,
                    "title": deal.company_name,
                    "deal_status": deal.status,
                    "current_valuation": deal.current_valuation,
                    "round_size": deal.round_size,
                    "commitment": deal.syndicate_commitment,
                    "business_model": deal.business_model,
                    "company_stage": deal.company_stage,
                    "minimum_investment": deal.minimum_investment, 
                    "instruments": deal.instrument_type,                     
                    "fund_raised_till_now": 0 ,
                    "logo_url": deal.logo_url,
                    "created_at": deal.created_at
                }
                for deal in closed_deals
            ]

            onhold_deals_list = [
                {
                    "deal_id": str(deal.id),
                    "description": deal.about_company,
                    "title": deal.company_name,
                    "deal_status": deal.status,
                    "current_valuation": deal.current_valuation,
                    "round_size": deal.round_size,
                    "commitment": deal.syndicate_commitment,
                    "business_model": deal.business_model,
                    "company_stage": deal.company_stage,
                    "minimum_investment": deal.minimum_investment, 
                    "instruments": deal.instrument_type,                     
                    "fund_raised_till_now": 0 ,
                    "logo_url": deal.logo_url,
                    "created_at": deal.created_at
                }
                for deal in onhold_deals
            ]
            return {
                "subadmin_id": str(subadmin.id),
                "subadmin_name": subadmin.name or "",
                "active_deals": active_deals_list,
                "closed_deals": closed_deals_list,
                "onhold_deals": onhold_deals_list,
                "success": True
            }
        except HTTPException as he:
            raise he
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to fetch deals overview: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch deals overview: {str(e)}"
            )

    async def get_members_statistics(
        self,
        session: AsyncSession,
        subadmin_id: UUID
    ) -> dict:
        try:
            # Fetch subadmin
            subadmin = await session.get(Subadmin, subadmin_id)
            if not subadmin:
                raise HTTPException(status_code=404, detail="Subadmin not found")

            # Fetch subadmin members (investors and startups)
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
                    "capital_committed": float(investor.capital_commitment or 0),
                    "kyc_status": investor.kyc_status
                }
                for investor in investors
            ]

            startups_stmt = select(User).where(
                and_(
                    User.fund_manager_id == subadmin_id,
                    User.role == Role.FOUNDER
                )
            ).options(joinedload(User.investments))
            startups_result = await session.execute(startups_stmt)
            startups = startups_result.unique().scalars().all()

            startups_list = [
                {
                    "user_id": str(startup.id),
                    "first_name": startup.first_name or "",
                    "last_name": startup.last_name or "",
                    "email": startup.email or "",
                    "capital_committed": float(startup.capital_commitment or 0),
                    "kyc_status": startup.kyc_status
                }
                for startup in startups
            ]

            subadmin_members = {
                "investors": investors_list,
                "startups": startups_list
            }

            investors_onboarded = len(investors)
            startups_onboarded = len(startups)
            investors_kyc_pending = sum(1 for investor in investors if investor.kyc_status == KycStatus.PENDING)
            startups_kyc_pending = sum(1 for startup in startups if startup.kyc_status == KycStatus.PENDING)
            investors_started_investing = sum(1 for investor in investors if len(investor.investments) > 0)
            startups_started_investing = sum(1 for startup in startups if len(startup.investments) > 0)

            return {
                "subadmin_id": str(subadmin.id),
                "subadmin_name": subadmin.name or "",
                "invite_code": subadmin.invite_code or "",
                "members": subadmin_members,
                "statistics": {
                    "investors_statistics": {
                        "onboarded": investors_onboarded,
                        "kyc_pending": investors_kyc_pending,
                        "started_investing": investors_started_investing
                    },
                    "startups_statistics": {
                        "onboarded": startups_onboarded,
                        "kyc_pending": startups_kyc_pending,
                        "started_investing": startups_started_investing
                    }
                },
                "success": True
            }
        except HTTPException as he:
            raise he
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to fetch members statistics: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch members statistics: {str(e)}"
            )

    async def add_members(
        self,
        session: AsyncSession,
        subadmin_id: UUID,
        email: str
    ) -> dict:
        try:
            # Fetch subadmin
            subadmin = await session.get(Subadmin, subadmin_id)
            if not subadmin:
                raise HTTPException(status_code=404, detail="Subadmin not found")

            # Fetch user by email (assuming email is unique)
            user_stmt = select(User).where(User.email == email)
            user_result = await session.execute(user_stmt)
            user = user_result.scalar_one_or_none()

            if not user:
                # If user not in user db, send invite
                email_response = await self.email_service.send_invitation_email(
                    email=email,
                    invite_code=subadmin.invite_code,
                    subadmin_name=subadmin.name or "",
                    user_name="",
                    apk_link="https://example.com/invite"
                )

                is_email_sent = email_response.get("success", False)
                if not is_email_sent:
                    raise HTTPException(status_code=400, detail="Failed to send invitation email")

                # Return placeholder response for non-existing user
                return {
                    "message": f"Invitation email sent to {email}",
                    "success": True
                }
            else:
                # If user exists, check if already a member of subadmin
                if user.fund_manager_id == subadmin_id:
                    logger.error(f"{user.first_name} {user.last_name} is already a member of subadmin {subadmin.name}")
                    return {
                        "message": f"{user.first_name} {user.last_name} is already a member of this subadmin",
                        "success": False
                    }

                else: 
                    # user exits but not a part of this subadmin
                
                    # Send invite to existing user as he is not in this subadmin team
                    email_response = await self.email_service.send_invitation_email(
                        email=email,
                        invite_code=subadmin.invite_code,
                        subadmin_name=subadmin.name or "",
                        user_name=f"{user.first_name or ''} {user.last_name or ''}".strip(),
                        apk_link="https://example.com/invite"
                    )

                    is_email_sent = email_response.get("success", False)
                    if not is_email_sent:
                        raise HTTPException(status_code=400, detail="Failed to send invitation email")

                    return {
                        "message": f"Invitation sent to {email}",
                        "success": True
                    }
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

    async def change_deal_status(
        self, 
        session: AsyncSession,
        deal_id: UUID,
        deal_status: DealStatus
    ): 
        try:
            deal = await session.get(Deal, deal_id)
            if not deal:
                raise HTTPException(status_code=404, detail="Deal not found")

            
            if deal.status == DealStatus.CLOSED:
                raise HTTPException(status_code=400, detail="You cannot change the status of a closed deal")

            deal.status = deal_status
            await session.commit()
            return {
                "message": f"Deal status updated to {deal_status.value}",
                "success": True
            }
        except HTTPException as he:
            logger.error(f"Failed to change deal status: {str(he)}")
            raise he
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to change deal status: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to change deal status: {str(e)}"
            )