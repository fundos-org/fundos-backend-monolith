from fastapi import HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func
from sqlalchemy.orm import joinedload
from src.logging.logging_setup import get_logger
from src.models.subadmin import Subadmin
from src.models.deal import Deal, DealStatus
from src.models.user import User, KycStatus, Role, OnboardingStatus
from src.models.kyc import KYC
from sqlalchemy import cast, String
from src.models.investment import Investment, InvestmentStatus
from src.models.transaction import Transaction, TransactionStatus, TransactionType
from src.services.s3 import S3Service
from src.services.email import EmailService
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy import and_ 
from src.configs.configs import aws_config, app_config




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
                "logo": subadmin.logo,
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

    async def get_deals_overview_paginated(
        self,
        session: AsyncSession,
        subadmin_id: UUID,
        active_page: int = 1,
        active_per_page: int = 10,
        closed_page: int = 1,
        closed_per_page: int = 10,
        onhold_page: int = 1,
        onhold_per_page: int = 10
    ) -> dict:
        try:
            subadmin = await session.get(Subadmin, subadmin_id)
            if not subadmin:
                raise HTTPException(status_code=404, detail="Subadmin not found")
            # Active deals
            active_stmt = select(Deal).where(
                Deal.fund_manager_id == subadmin_id,
                cast(Deal.status, String) == "OPEN"
            )
            active_result = await session.execute(active_stmt)
            active_deals = active_result.scalars().all()
            total_active = len(active_deals)
            total_active_pages = (total_active + active_per_page - 1) // active_per_page
            active_offset = (active_page - 1) * active_per_page
            paginated_active = active_deals[active_offset:active_offset+active_per_page]
            active_deals_list = [
                {
                    "deal_id": str(deal.id),
                    "description": deal.about_company or "",
                    "title": deal.company_name or "",
                    "deal_status": deal.status.value if hasattr(deal.status, 'value') else str(deal.status),
                    "current_valuation": deal.current_valuation or 0,
                    "round_size": deal.round_size or 0,
                    "commitment": deal.syndicate_commitment or 0,
                    "business_model": deal.business_model.value if hasattr(deal.business_model, 'value') else str(deal.business_model),
                    "company_stage": deal.company_stage.value if hasattr(deal.company_stage, 'value') else str(deal.company_stage),
                    "logo_url": deal.logo_url or "",
                    "created_at": deal.created_at.strftime("%Y-%m-%d") if deal.created_at else ""
                }
                for deal in paginated_active
            ]
            active_pagination = {
                "page": active_page,
                "per_page": active_per_page,
                "total_records": total_active,
                "total_pages": total_active_pages,
                "has_next": active_page < total_active_pages,
                "has_prev": active_page > 1
            }
            # Closed deals
            closed_stmt = select(Deal).where(
                Deal.fund_manager_id == subadmin_id,
                cast(Deal.status, String) == "CLOSED"
            )
            closed_result = await session.execute(closed_stmt)
            closed_deals = closed_result.scalars().all()
            total_closed = len(closed_deals)
            total_closed_pages = (total_closed + closed_per_page - 1) // closed_per_page
            closed_offset = (closed_page - 1) * closed_per_page
            paginated_closed = closed_deals[closed_offset:closed_offset+closed_per_page]
            closed_deals_list = [
                {
                    "deal_id": str(deal.id),
                    "description": deal.about_company or "",
                    "title": deal.company_name or "",
                    "deal_status": deal.status.value if hasattr(deal.status, 'value') else str(deal.status),
                    "current_valuation": deal.current_valuation or 0,
                    "round_size": deal.round_size or 0,
                    "commitment": deal.syndicate_commitment or 0,
                    "business_model": deal.business_model.value if hasattr(deal.business_model, 'value') else str(deal.business_model),
                    "company_stage": deal.company_stage.value if hasattr(deal.company_stage, 'value') else str(deal.company_stage),
                    "logo_url": deal.logo_url or "",
                    "created_at": deal.created_at.strftime("%Y-%m-%d") if deal.created_at else ""
                }
                for deal in paginated_closed
            ]
            closed_pagination = {
                "page": closed_page,
                "per_page": closed_per_page,
                "total_records": total_closed,
                "total_pages": total_closed_pages,
                "has_next": closed_page < total_closed_pages,
                "has_prev": closed_page > 1
            }
            # Onhold deals
            onhold_stmt = select(Deal).where(
                Deal.fund_manager_id == subadmin_id,
                cast(Deal.status, String) == "ON_HOLD"
            )
            onhold_result = await session.execute(onhold_stmt)
            onhold_deals = onhold_result.scalars().all()
            total_onhold = len(onhold_deals)
            total_onhold_pages = (total_onhold + onhold_per_page - 1) // onhold_per_page
            onhold_offset = (onhold_page - 1) * onhold_per_page
            paginated_onhold = onhold_deals[onhold_offset:onhold_offset+onhold_per_page]
            onhold_deals_list = [
                {
                    "deal_id": str(deal.id),
                    "description": deal.about_company or "",
                    "title": deal.company_name or "",
                    "deal_status": deal.status.value if hasattr(deal.status, 'value') else str(deal.status),
                    "current_valuation": deal.current_valuation or 0,
                    "round_size": deal.round_size or 0,
                    "commitment": deal.syndicate_commitment or 0,
                    "business_model": deal.business_model.value if hasattr(deal.business_model, 'value') else str(deal.business_model),
                    "company_stage": deal.company_stage.value if hasattr(deal.company_stage, 'value') else str(deal.company_stage),
                    "logo_url": deal.logo_url or "",
                    "created_at": deal.created_at.strftime("%Y-%m-%d") if deal.created_at else ""
                }
                for deal in paginated_onhold
            ]
            onhold_pagination = {
                "page": onhold_page,
                "per_page": onhold_per_page,
                "total_records": total_onhold,
                "total_pages": total_onhold_pages,
                "has_next": onhold_page < total_onhold_pages,
                "has_prev": onhold_page > 1
            }
            return {
                "subadmin_id": str(subadmin.id),
                "subadmin_name": subadmin.name or "",
                "active_deals": active_deals_list,
                "closed_deals": closed_deals_list,
                "onhold_deals": onhold_deals_list,
                "active_pagination": active_pagination,
                "closed_pagination": closed_pagination,
                "onhold_pagination": onhold_pagination,
                "success": True
            }
        except HTTPException as he:
            raise he
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to fetch paginated deals overview: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch paginated deals overview: {str(e)}"
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
                    apk_link=app_config.apk_link
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
                        apk_link=app_config.apk_link
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

    async def get_investors_list(
        self,
        session: AsyncSession,
        subadmin_id: UUID,
        page: int = 1,
        per_page: int = 20
    ) -> dict:
        try:
            # Fetch subadmin
            subadmin = await session.get(Subadmin, subadmin_id)
            if not subadmin:
                raise HTTPException(status_code=404, detail="Subadmin not found")

            # Calculate offset for pagination
            offset = (page - 1) * per_page

            # Get total count of investors with onboarded status
            total_count_stmt = select(func.count(User.id)).where(
                and_(
                    User.fund_manager_id == subadmin_id,
                    User.role == Role.INVESTOR,
                    # User.onboarding_status == OnboardingStatus.Completed
                    cast(User.onboarding_status, String) == OnboardingStatus.Completed
                )
            )
            total_count_result = await session.execute(total_count_stmt)
            total_records = total_count_result.scalar() or 0

            # Calculate total pages
            total_pages = (total_records + per_page - 1) // per_page

            # Fetch investors with pagination
            investors_stmt = select(User).where(
                and_(
                    User.fund_manager_id == subadmin_id,
                    User.role == Role.INVESTOR,
                    # User.onboarding_status == OnboardingStatus.Completed
                    cast(User.onboarding_status, String) == OnboardingStatus.Completed
                )
            ).options(joinedload(User.investments)).offset(offset).limit(per_page)
            
            investors_result = await session.execute(investors_stmt)
            investors = investors_result.unique().scalars().all()

            # Prepare investors list
            investors_list = []
            for investor in investors:
                # Count deals invested
                deals_invested = len(investor.investments)
                
                investors_list.append({
                    "investor_id": str(investor.id),
                    "name": investor.full_name or f"{investor.first_name or ''} {investor.last_name or ''}".strip(),
                    "mail": investor.email or "",
                    "type": investor.investor_type.value if investor.investor_type else "",
                    "deals_invested": deals_invested,
                    "kyc_status": investor.kyc_status,
                    "mca_key": investor.mca_key or "",
                    "joined_on": investor.created_at.strftime("%Y-%m-%d") if investor.created_at else "",
                    "profile_pic": investor.profile_image_url or "",
                    "capital_commitment": investor.capital_commitment or 0,
                })

            # Prepare pagination info
            pagination_info = {
                "page": page,
                "per_page": per_page,
                "total_records": total_records,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }

            return {
                "subadmin_id": str(subadmin.id),
                "subadmin_name": subadmin.name or "",
                "investors": investors_list,
                "pagination": pagination_info,
                "success": True
            }
        except HTTPException as he:
            raise he
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to fetch investors list: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch investors list: {str(e)}"
            )

    async def get_investors_metadata(
        self,
        session: AsyncSession,
        subadmin_id: UUID
    ) -> dict:
        try:
            # Fetch subadmin
            subadmin = await session.get(Subadmin, subadmin_id)
            if not subadmin:
                raise HTTPException(status_code=404, detail="Subadmin not found")

            # Calculate metadata
            all_investors_stmt = select(User).where(
                and_(
                    User.fund_manager_id == subadmin_id,
                    User.role == Role.INVESTOR
                )
            ).options(joinedload(User.investments))
            all_investors_result = await session.execute(all_investors_stmt)
            all_investors = all_investors_result.unique().scalars().all()

            investor_onboarded = sum(1 for inv in all_investors if inv.onboarding_status == OnboardingStatus.Completed)
            
            # this will return the count of kyc pending where role is investor and kyc is pending and onboarding status is completed
            kyc_pending = 0
            for inv in all_investors:
                if inv.role == Role.INVESTOR and inv.onboarding_status == OnboardingStatus.Completed and inv.kyc_status == KycStatus.PENDING:
                    kyc_pending += 1
            
            started_investing = sum(1 for inv in all_investors if len(inv.investments) > 0)

            return {
                "subadmin_id": str(subadmin.id),
                "subadmin_name": subadmin.name or "",
                "metadata": {
                    "investor_onboarded": investor_onboarded,
                    "kyc_pending": kyc_pending,
                    "started_investing": started_investing
                },
                "success": True
            }
        except HTTPException as he:
            raise he
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to fetch investors metadata: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch investors metadata: {str(e)}"
            )

    async def delete_investor(
        self,
        session: AsyncSession,
        subadmin_id: UUID,
        investor_id: UUID
    ) -> dict:
        try:
            # Fetch subadmin
            subadmin = await session.get(Subadmin, subadmin_id)
            if not subadmin:
                raise HTTPException(status_code=404, detail="Subadmin not found")

            # Fetch investor
            investor = await session.get(User, investor_id)
            if not investor:
                raise HTTPException(status_code=404, detail="Investor not found")

            # Verify investor belongs to this subadmin
            if investor.fund_manager_id != subadmin_id:
                raise HTTPException(status_code=403, detail="Investor does not belong to this subadmin")

            # Verify investor role
            if investor.role != Role.INVESTOR:
                raise HTTPException(status_code=400, detail="User is not an investor")

            # Check if investor has any active investments
            investments_stmt = select(Investment).where(
                and_(
                    Investment.investor_id == investor_id,
                    cast(Investment.status, String).in_([InvestmentStatus.PENDING.name, InvestmentStatus.COMPLETED.name])
                )
            )
            investments_result = await session.execute(investments_stmt)
            active_investments = investments_result.scalars().all()

            if active_investments:
                raise HTTPException(
                    status_code=400, 
                    detail="Cannot delete investor with active investments"
                )

            # Store investor details for response
            investor_name = investor.full_name or f"{investor.first_name or ''} {investor.last_name or ''}".strip()
            investor_email = investor.email or ""

            # Delete investor
            await session.delete(investor)
            await session.commit()

            logger.info(f"Investor {investor_name} ({investor_email}) deleted by subadmin {subadmin.name}")

            return {
                "subadmin_id": str(subadmin.id),
                "investor_id": str(investor_id),
                "message": f"Investor {investor_name} has been successfully deleted",
                "success": True
            }
        except HTTPException as he:
            raise he
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to delete investor: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete investor: {str(e)}"
            )

    async def update_investor(
        self,
        session: AsyncSession,
        subadmin_id: UUID,
        investor_id: UUID,
        update_data: dict
    ) -> dict:
        try:
            # Fetch subadmin
            subadmin = await session.get(Subadmin, subadmin_id)
            if not subadmin:
                raise HTTPException(status_code=404, detail="Subadmin not found")

            # Fetch investor
            investor = await session.get(User, investor_id)
            if not investor:
                raise HTTPException(status_code=404, detail="Investor not found")

            # Verify investor belongs to this subadmin
            if investor.fund_manager_id != subadmin_id:
                raise HTTPException(status_code=403, detail="Investor does not belong to this subadmin")

            # Verify investor role
            if investor.role != Role.INVESTOR:
                raise HTTPException(status_code=400, detail="User is not an investor")

            # Update user data
            if update_data:
                # Update first_name and last_name
                if update_data.get("first_name") is not None:
                    investor.first_name = update_data["first_name"]
                if update_data.get("last_name") is not None:
                    investor.last_name = update_data["last_name"]
                
                # Update full_name (concatenate first_name and last_name)
                if update_data.get("first_name") is not None or update_data.get("last_name") is not None:
                    first_name = update_data.get("first_name", investor.first_name) or ""
                    last_name = update_data.get("last_name", investor.last_name) or ""
                    investor.full_name = f"{first_name} {last_name}".strip()

                # Update other user fields
                if update_data.get("occupation") is not None:
                    investor.occupation = update_data["occupation"]
                if update_data.get("income_source") is not None:
                    investor.income_source = update_data["income_source"]
                if update_data.get("annual_income") is not None:
                    investor.annual_income = update_data["annual_income"]
                if update_data.get("capital_commitment") is not None:
                    investor.capital_commitment = update_data["capital_commitment"]

                # Update updated_at timestamp
                investor.updated_at = datetime.now()

            await session.commit()

            # Get updated investor name for response
            investor_name = investor.full_name or f"{investor.first_name or ''} {investor.last_name or ''}".strip()

            logger.info(f"Investor {investor_name} updated by subadmin {subadmin.name}")

            return {
                "subadmin_id": str(subadmin.id),
                "investor_id": str(investor_id),
                "message": f"Investor {investor_name} has been successfully updated",
                "success": True
            }
        except HTTPException as he:
            raise he
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to update investor: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update investor: {str(e)}"
            )

    async def get_investor_about_info(
        self,
        session: AsyncSession,
        investor_id: UUID
    ) -> dict:
        try:
            # Fetch investor
            investor = await session.get(User, investor_id)
            if not investor:
                raise HTTPException(status_code=404, detail="Investor not found")

            # Verify investor role
            if investor.role != Role.INVESTOR:
                raise HTTPException(status_code=400, detail="User is not an investor")

            # Fetch KYC record for this investor
            kyc_stmt = select(KYC).where(KYC.user_id == investor_id)
            kyc_result = await session.execute(kyc_stmt)
            kyc_record = kyc_result.scalar_one_or_none()

            # Prepare personal details
            personal_details = {
                "first_name": investor.first_name,
                "last_name": investor.last_name,
                "email": investor.email,
                "phone_number": investor.phone_number,
                "pan_number": kyc_record.pan_number if kyc_record else None,
                "aadhaar_number": kyc_record.aadhaar_number if kyc_record else None
            }

            # Prepare bank details
            bank_details = {
                "bank_account_number": kyc_record.bank_account_number if kyc_record else None,
                "bank_ifsc": kyc_record.bank_ifsc if kyc_record else None,
                "account_holder_name": "John Doe"  # Mock data
            }

            # Prepare professional background
            professional_background = {
                "occupation": investor.occupation,
                "income_source": investor.income_source,
                "annual_income": investor.annual_income,
                "capital_commitment": investor.capital_commitment
            }

            logger.info(f"Investor info fetched for investor ID: {investor_id}")

            return {
                "investor_id": str(investor_id),
                "personal_details": personal_details,
                "bank_details": bank_details,
                "professional_background": professional_background,
                "success": True
            }
        except HTTPException as he:
            raise he
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to fetch investor info: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch investor info: {str(e)}"
            )

    async def get_investor_investments_info(
        self,
        session: AsyncSession,
        investor_id: UUID,
        page: int = 1,
        per_page: int = 20
    ) -> dict:
        try:
            investor = await session.get(User, investor_id)
            if not investor:
                raise HTTPException(status_code=404, detail="Investor not found")
            if investor.role != Role.INVESTOR:
                raise HTTPException(status_code=400, detail="User is not an investor")
            investments_stmt = select(Investment).where(
                Investment.investor_id == investor_id
            ).options(joinedload(Investment.deal))
            investments_result = await session.execute(investments_stmt)
            investments = investments_result.unique().scalars().all()
            total_records = len(investments)
            total_pages = (total_records + per_page - 1) // per_page
            offset = (page - 1) * per_page
            paginated_investments = investments[offset:offset+per_page]
            deals_list = []
            for investment in paginated_investments:
                if investment.deal:
                    deals_list.append({
                        "company_name": investment.deal.company_name or "",
                        "about_company": investment.deal.about_company or "",
                        "industry": investment.deal.industry or "",
                        "company_stage": investment.deal.company_stage or "",
                        "logo_url": investment.deal.logo_url or "",
                        "status": investment.deal.status.value if investment.deal.status else "",
                        "created_at": investment.deal.created_at.strftime("%Y-%m-%d") if investment.deal.created_at else "",
                        "deal_capital_commitment": 500000.0,
                        "equity": 15.5,
                        "term_sheet": "https://example.com/term-sheet.pdf"
                    })
            pagination_info = {
                "page": page,
                "per_page": per_page,
                "total_records": total_records,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
            logger.info(f"Investor investments info fetched for investor ID: {investor_id}")
            return {
                "investor_id": str(investor_id),
                "deals": deals_list,
                "pagination": pagination_info,
                "success": True
            }
        except HTTPException as he:
            raise he
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to fetch investor investments info: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch investor investments info: {str(e)}"
            )

    async def get_investor_investments_metadata(
        self,
        session: AsyncSession,
        investor_id: UUID
    ) -> dict:
        try:
            # Fetch investor
            investor = await session.get(User, investor_id)
            if not investor:
                raise HTTPException(status_code=404, detail="Investor not found")

            # Verify investor role
            if investor.role != Role.INVESTOR:
                raise HTTPException(status_code=400, detail="User is not an investor")

            # Count total deals for this investor
            total_deals_stmt = select(func.count(Investment.id)).where(
                Investment.investor_id == investor_id
            )
            total_deals_result = await session.execute(total_deals_stmt)
            total_deals = total_deals_result.scalar() or 0

            # Prepare metadata
            metadata = {
                "first_name": investor.first_name,
                "last_name": investor.last_name,
                "investor_type": investor.investor_type.value if investor.investor_type else "",
                "role": investor.role.value if investor.role else "",
                "capital_commitment": investor.capital_commitment,
                "profile_image_url": investor.profile_image_url,
                "created_at": investor.created_at.strftime("%Y-%m-%d") if investor.created_at else "",
                "total_deals": total_deals
            }

            logger.info(f"Investor investments metadata fetched for investor ID: {investor_id}")

            return {
                "investor_id": str(investor_id),
                "metadata": metadata,
                "success": True
            }
        except HTTPException as he:
            raise he
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to fetch investor investments metadata: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch investor investments metadata: {str(e)}"
            )

    async def get_investor_transactions(
        self,
        session: AsyncSession,
        investor_id: UUID,
        page: int = 1,
        per_page: int = 20
    ) -> dict:
        try:
            investor = await session.get(User, investor_id)
            if not investor:
                raise HTTPException(status_code=404, detail="Investor not found")
            if investor.role != Role.INVESTOR:
                raise HTTPException(status_code=400, detail="User is not an investor")
            transactions_stmt = select(Transaction).join(Investment).where(
                Investment.investor_id == investor_id
            )
            transactions_result = await session.execute(transactions_stmt)
            transactions = transactions_result.unique().scalars().all()
            total_records = len(transactions)
            total_pages = (total_records + per_page - 1) // per_page
            offset = (page - 1) * per_page
            paginated_transactions = transactions[offset:offset+per_page]
            transactions_list = []
            for transaction in paginated_transactions:
                transactions_list.append({
                    "transaction_type": transaction.transaction_type.value if transaction.transaction_type else "",
                    "amount": transaction.amount,
                    "currency": transaction.currency,
                    "status": transaction.status.value if transaction.status else "",
                    "created_at": transaction.created_at.strftime("%Y-%m-%d %H:%M:%S") if transaction.created_at else "",
                    "invitation_code": investor.invitation_code
                })
            pagination_info = {
                "page": page,
                "per_page": per_page,
                "total_records": total_records,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
            logger.info(f"Investor transactions fetched for investor ID: {investor_id}")
            return {
                "investor_id": str(investor_id),
                "transactions": transactions_list,
                "pagination": pagination_info,
                "success": True
            }
        except HTTPException as he:
            raise he
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to fetch investor transactions: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch investor transactions: {str(e)}"
            )

    async def get_investor_documents_info(
        self,
        session: AsyncSession,
        investor_id: UUID
    ) -> dict:
        try:
            # Fetch investor
            investor = await session.get(User, investor_id)
            if not investor:
                raise HTTPException(status_code=404, detail="Investor not found")

            # Verify investor role
            if investor.role != Role.INVESTOR:
                raise HTTPException(status_code=400, detail="User is not an investor")

            # Prepare documents info
            documents_info = {
                "mca_key": investor.mca_key,
                "share_certificate_key": "SHARE_CERT_123456",  # Mock data
                "term_sheet_key": "TERM_SHEET_789012"  # Mock data
            }

            logger.info(f"Investor documents info fetched for investor ID: {investor_id}")

            return {
                "investor_id": str(investor_id),
                "documents": documents_info,
                "success": True
            }
        except HTTPException as he:
            raise he
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to fetch investor documents info: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch investor documents info: {str(e)}"
            )

    async def mark_deal_inactive(
        self,
        session: AsyncSession,
        deal_id: UUID
    ) -> dict:
        try:
            deal = await session.get(Deal, deal_id)
            if not deal:
                raise HTTPException(status_code=404, detail="Deal not found")
            if deal.status == DealStatus.CLOSED:
                raise HTTPException(status_code=400, detail="Deal is already closed")
            deal.status = DealStatus.CLOSED
            deal.updated_at = datetime.now()
            await session.commit()
            logger.info(f"Deal {deal.company_name} marked as inactive")
            return {
                "deal_id": str(deal_id),
                "message": f"Deal {deal.company_name} has been successfully marked as inactive",
                "success": True
            }
        except HTTPException as he:
            raise he
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to mark deal inactive: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to mark deal inactive: {str(e)}"
            )

    async def get_deal_details(
        self,
        session: AsyncSession,
        deal_id: UUID
    ) -> dict:
        try:
            deal = await session.get(Deal, deal_id)
            if not deal:
                raise HTTPException(status_code=404, detail="Deal not found")
            deal_details = {
                "logo_url": deal.logo_url,
                "company_name": deal.company_name,
                "about_company": deal.about_company,
                "company_website": deal.company_website,
                "problem_statement": deal.problem_statement,
                "industry": deal.industry.value if deal.industry else None,
                "business_model": deal.business_model.value if deal.business_model else None,
                "company_stage": deal.company_stage.value if deal.company_stage else None,
                "current_valuation": deal.current_valuation,
                "round_size": deal.round_size,
                "syndicate_commitment": deal.syndicate_commitment,
                "conversion_terms": deal.conversion_terms,
                "instrument_type": deal.instrument_type.value if deal.instrument_type else None,
                "pitch_deck_url": deal.pitch_deck_url,
                "pitch_video_url": deal.pitch_video_url
            }
            logger.info(f"Deal details fetched for deal ID: {deal_id}")
            return {
                "deal_id": str(deal_id),
                "deal_details": deal_details,
                "success": True
            }
        except HTTPException as he:
            raise he
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to fetch deal details: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch deal details: {str(e)}"
            )

    async def edit_deal(
        self,
        session: AsyncSession,
        deal_id: UUID,
        update_data: dict
    ) -> dict:
        try:
            deal = await session.get(Deal, deal_id)
            if not deal:
                raise HTTPException(status_code=404, detail="Deal not found")
            if update_data.get("logo_url") is not None:
                deal.logo_url = update_data["logo_url"]
            if update_data.get("company_name") is not None:
                deal.company_name = update_data["company_name"]
            if update_data.get("about_company") is not None:
                deal.about_company = update_data["about_company"]
            if update_data.get("company_website") is not None:
                deal.company_website = update_data["company_website"]
            if update_data.get("problem_statement") is not None:
                deal.problem_statement = update_data["problem_statement"]
            if update_data.get("industry") is not None:
                deal.industry = update_data["industry"]
            if update_data.get("business_model") is not None:
                deal.business_model = update_data["business_model"]
            if update_data.get("company_stage") is not None:
                deal.company_stage = update_data["company_stage"]
            if update_data.get("current_valuation") is not None:
                deal.current_valuation = update_data["current_valuation"]
            if update_data.get("round_size") is not None:
                deal.round_size = update_data["round_size"]
            if update_data.get("syndicate_commitment") is not None:
                deal.syndicate_commitment = update_data["syndicate_commitment"]
            if update_data.get("conversion_terms") is not None:
                deal.conversion_terms = update_data["conversion_terms"]
            if update_data.get("instrument_type") is not None:
                deal.instrument_type = update_data["instrument_type"]
            if update_data.get("pitch_deck_url") is not None:
                deal.pitch_deck_url = update_data["pitch_deck_url"]
            if update_data.get("pitch_video_url") is not None:
                deal.pitch_video_url = update_data["pitch_video_url"]
            deal.updated_at = datetime.now()
            await session.commit()
            logger.info(f"Deal details updated for {deal.company_name}")
            return {
                "deal_id": str(deal_id),
                "message": f"Deal details have been successfully updated",
                "success": True
            }
        except HTTPException as he:
            raise he
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to update deal details: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update deal details: {str(e)}"
            )

    async def get_deal_about_info(
        self,
        session: AsyncSession,
        deal_id: UUID
    ) -> dict:
        try:
            deal = await session.get(Deal, deal_id)
            if not deal:
                raise HTTPException(status_code=404, detail="Deal not found")
            about_info = {
                "company_name": deal.company_name,
                "company_website": deal.company_website,
                "company_email": "contact@example.com",
                "industry": deal.industry.value if deal.industry else None,
                "business_model": deal.business_model.value if deal.business_model else None
            }
            logger.info(f"Deal about info fetched for deal ID: {deal_id}")
            return {
                "deal_id": str(deal_id),
                "about_info": about_info,
                "success": True
            }
        except HTTPException as he:
            raise he
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to fetch deal about info: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch deal about info: {str(e)}"
            )

    async def get_deal_investors(
        self,
        session: AsyncSession,
        deal_id: UUID,
        page: int = 1,
        per_page: int = 20
    ) -> dict:
        try:
            # Fetch deal
            deal = await session.get(Deal, deal_id)
            if not deal:
                raise HTTPException(status_code=404, detail="Deal not found")

            # Calculate offset for pagination
            offset = (page - 1) * per_page

            # Mock data for investors (since no real data in database)
            mock_investors = [
                {
                    "investor_id": "inv-001",
                    "first_name": "John",
                    "last_name": "Doe",
                    "investor_type": "individual",
                    "commitments": 50000.0,
                    "created_at": "2024-01-15",
                    "status": "active",
                    "term_sheet_key": "TERM_SHEET_001",
                    "deal_investor_status": 1
                },
                {
                    "investor_id": "inv-002",
                    "first_name": "Jane",
                    "last_name": "Smith",
                    "investor_type": "entity",
                    "commitments": 100000.0,
                    "created_at": "2024-01-20",
                    "status": "pending",
                    "term_sheet_key": "TERM_SHEET_002",
                    "deal_investor_status": 0
                },
                {
                    "investor_id": "inv-003",
                    "first_name": "Mike",
                    "last_name": "Johnson",
                    "investor_type": "individual",
                    "commitments": 75000.0,
                    "created_at": "2024-01-25",
                    "status": "active",
                    "term_sheet_key": "TERM_SHEET_003",
                    "deal_investor_status": 1
                }
            ]

            # Apply pagination to mock data
            total_records = len(mock_investors)
            total_pages = (total_records + per_page - 1) // per_page
            paginated_investors = mock_investors[offset:offset + per_page]

            # Prepare pagination info
            pagination_info = {
                "page": page,
                "per_page": per_page,
                "total_records": total_records,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }

            logger.info(f"Deal investors fetched for deal ID: {deal_id}")

            return {
                "deal_id": str(deal_id),
                "investors": paginated_investors,
                "pagination": pagination_info,
                "success": True
            }
        except HTTPException as he:
            raise he
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to fetch deal investors: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch deal investors: {str(e)}"
            )

    async def get_deal_transactions(
        self,
        session: AsyncSession,
        deal_id: UUID,
        page: int = 1,
        per_page: int = 20
    ) -> dict:
        try:
            # Fetch deal
            deal = await session.get(Deal, deal_id)
            if not deal:
                raise HTTPException(status_code=404, detail="Deal not found")

            # Calculate offset for pagination
            offset = (page - 1) * per_page

            # Mock data for transactions (since no real data in database)
            mock_transactions = [
                {
                    "transaction_id": "txn-001",
                    "invitation_code": "INVITE_001",
                    "transaction_type": "payment",
                    "amount": 50000.0,
                    "created_at": "2024-01-15 10:30:00",
                    "status": "completed"
                },
                {
                    "transaction_id": "txn-002",
                    "invitation_code": "INVITE_002",
                    "transaction_type": "payment",
                    "amount": 100000.0,
                    "created_at": "2024-01-20 14:45:00",
                    "status": "pending"
                },
                {
                    "transaction_id": "txn-003",
                    "invitation_code": "INVITE_003",
                    "transaction_type": "refund",
                    "amount": 25000.0,
                    "created_at": "2024-01-25 09:15:00",
                    "status": "completed"
                }
            ]

            # Apply pagination to mock data
            total_records = len(mock_transactions)
            total_pages = (total_records + per_page - 1) // per_page
            paginated_transactions = mock_transactions[offset:offset + per_page]

            # Prepare pagination info
            pagination_info = {
                "page": page,
                "per_page": per_page,
                "total_records": total_records,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }

            logger.info(f"Deal transactions fetched for deal ID: {deal_id}")

            return {
                "deal_id": str(deal_id),
                "transactions": paginated_transactions,
                "pagination": pagination_info,
                "success": True
            }
        except HTTPException as he:
            raise he
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to fetch deal transactions: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch deal transactions: {str(e)}"
            )

    async def get_deal_documents(
        self,
        session: AsyncSession,
        deal_id: UUID
    ) -> dict:
        try:
            # Fetch deal
            deal = await session.get(Deal, deal_id)
            if not deal:
                raise HTTPException(status_code=404, detail="Deal not found")

            # Prepare documents info (mock data)
            documents_info = {
                "pitchdeck_final_key": "PITCH_DECK_FINAL_123",
                "video_pitch_key": "VIDEO_PITCH_456"
            }

            logger.info(f"Deal documents fetched for deal ID: {deal_id}")

            return {
                "deal_id": str(deal_id),
                "documents": documents_info,
                "success": True
            }
        except HTTPException as he:
            raise he
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to fetch deal documents: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch deal documents: {str(e)}"
            )

    async def get_welcome_mail(
        self,
        session: AsyncSession,
        subadmin_id: UUID
    ) -> dict:
        try:
            # Fetch subadmin
            subadmin = await session.get(Subadmin, subadmin_id)
            if not subadmin:
                raise HTTPException(status_code=404, detail="Subadmin not found")

            # Mock data for welcome mail
            welcome_mail = {
                "subject": "Welcome to Fundos - Your Investment Journey Begins",
                "body": "Dear {investor_name},\n\nWelcome to Fundos! We're excited to have you join our investment platform.\n\nThis is a mock welcome email template that can be customized by subadmins.\n\nBest regards,\nThe Fundos Team"
            }

            logger.info(f"Welcome mail fetched for subadmin ID: {subadmin_id}")

            return {
                "subadmin_id": str(subadmin.id),
                "welcome_mail": welcome_mail,
                "success": True
            }
        except HTTPException as he:
            raise he
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to fetch welcome mail: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch welcome mail: {str(e)}"
            )

    async def update_welcome_mail(
        self,
        session: AsyncSession,
        subadmin_id: UUID,
        update_data: dict
    ) -> dict:
        try:
            # Fetch subadmin
            subadmin = await session.get(Subadmin, subadmin_id)
            if not subadmin:
                raise HTTPException(status_code=404, detail="Subadmin not found")

            # Mock update - in real implementation, this would update database
            subject = update_data.get("subject", "")
            body = update_data.get("body", "")

            logger.info(f"Welcome mail updated for subadmin ID: {subadmin_id}")

            return {
                "subadmin_id": str(subadmin.id),
                "message": "Welcome mail has been successfully updated",
                "success": True
            }
        except HTTPException as he:
            raise he
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to update welcome mail: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update welcome mail: {str(e)}"
            )

    async def get_onboarding_mail(
        self,
        session: AsyncSession,
        subadmin_id: UUID
    ) -> dict:
        try:
            # Fetch subadmin
            subadmin = await session.get(Subadmin, subadmin_id)
            if not subadmin:
                raise HTTPException(status_code=404, detail="Subadmin not found")

            # Mock data for onboarding mail
            onboarding_mail = {
                "subject": "Complete Your Onboarding - Fundos Investment Platform",
                "body": "Dear {investor_name},\n\nThank you for joining Fundos! To complete your onboarding process, please follow the steps below:\n\n1. Verify your email address\n2. Complete your KYC\n3. Set up your investment preferences\n\nThis is a mock onboarding email template.\n\nBest regards,\nThe Fundos Team"
            }

            logger.info(f"Onboarding mail fetched for subadmin ID: {subadmin_id}")

            return {
                "subadmin_id": str(subadmin.id),
                "onboarding_mail": onboarding_mail,
                "success": True
            }
        except HTTPException as he:
            raise he
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to fetch onboarding mail: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch onboarding mail: {str(e)}"
            )

    async def update_onboarding_mail(
        self,
        session: AsyncSession,
        subadmin_id: UUID,
        update_data: dict
    ) -> dict:
        try:
            # Fetch subadmin
            subadmin = await session.get(Subadmin, subadmin_id)
            if not subadmin:
                raise HTTPException(status_code=404, detail="Subadmin not found")

            # Mock update - in real implementation, this would update database
            subject = update_data.get("subject", "")
            body = update_data.get("body", "")

            logger.info(f"Onboarding mail updated for subadmin ID: {subadmin_id}")

            return {
                "subadmin_id": str(subadmin.id),
                "message": "Onboarding mail has been successfully updated",
                "success": True
            }
        except HTTPException as he:
            raise he
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to update onboarding mail: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update onboarding mail: {str(e)}"
            )

    async def get_consent_mail(
        self,
        session: AsyncSession,
        subadmin_id: UUID
    ) -> dict:
        try:
            # Fetch subadmin
            subadmin = await session.get(Subadmin, subadmin_id)
            if not subadmin:
                raise HTTPException(status_code=404, detail="Subadmin not found")

            # Mock data for consent mail
            consent_mail = {
                "subject": "Investment Consent Required - Fundos Platform",
                "body": "Dear {investor_name},\n\nWe require your consent to proceed with the investment process. Please review the terms and conditions carefully.\n\nThis is a mock consent email template for investment agreements.\n\nBest regards,\nThe Fundos Team"
            }

            logger.info(f"Consent mail fetched for subadmin ID: {subadmin_id}")

            return {
                "subadmin_id": str(subadmin.id),
                "consent_mail": consent_mail,
                "success": True
            }
        except HTTPException as he:
            raise he
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to fetch consent mail: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch consent mail: {str(e)}"
            )

    async def update_consent_mail(
        self,
        session: AsyncSession,
        subadmin_id: UUID,
        update_data: dict
    ) -> dict:
        try:
            # Fetch subadmin
            subadmin = await session.get(Subadmin, subadmin_id)
            if not subadmin:
                raise HTTPException(status_code=404, detail="Subadmin not found")

            # Mock update - in real implementation, this would update database
            subject = update_data.get("subject", "")
            body = update_data.get("body", "")

            logger.info(f"Consent mail updated for subadmin ID: {subadmin_id}")

            return {
                "subadmin_id": str(subadmin.id),
                "message": "Consent mail has been successfully updated",
                "success": True
            }
        except HTTPException as he:
            raise he
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to update consent mail: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update consent mail: {str(e)}"
            )
        
    async def get_combined_emails(
        self,
        session: AsyncSession,
        subadmin_id: UUID
    ) -> dict:
        try:
            # Fetch subadmin
            subadmin = await session.get(Subadmin, subadmin_id)
            if not subadmin:
                raise HTTPException(status_code=404, detail="Subadmin not found")

            # Mock data for all email templates
            welcome_mail = {
                "subject": "Welcome to Fundos - Your Investment Journey Begins",
                "body": "Dear {investor_name},\n\nWelcome to Fundos! We're excited to have you join our investment platform.\n\nThis is a mock welcome email template that can be customized by subadmins.\n\nBest regards,\nThe Fundos Team"
            }

            onboarding_mail = {
                "subject": "Complete Your Onboarding - Fundos Investment Platform",
                "body": "Dear {investor_name},\n\nThank you for joining Fundos! To complete your onboarding process, please follow the steps below:\n\n1. Verify your email address\n2. Complete your KYC\n3. Set up your investment preferences\n\nThis is a mock onboarding email template.\n\nBest regards,\nThe Fundos Team"
            }

            consent_mail = {
                "subject": "Investment Consent Required - Fundos Platform",
                "body": "Dear {investor_name},\n\nWe require your consent to proceed with the investment process. Please review the terms and conditions carefully.\n\nThis is a mock consent email template for investment agreements.\n\nBest regards,\nThe Fundos Team"
            }

            logger.info(f"Combined emails fetched for subadmin ID: {subadmin_id}")

            return {
                "subadmin_id": str(subadmin.id),
                "welcome_mail": welcome_mail,
                "onboarding_mail": onboarding_mail,
                "consent_mail": consent_mail,
                "success": True
            }
        except HTTPException as he:
            raise he
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to fetch combined emails: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch combined emails: {str(e)}"
            )

    async def update_combined_emails(
        self,
        session: AsyncSession,
        subadmin_id: UUID,
        update_data: dict
    ) -> dict:
        try:
            # Fetch subadmin
            subadmin = await session.get(Subadmin, subadmin_id)
            if not subadmin:
                raise HTTPException(status_code=404, detail="Subadmin not found")

            # Mock update - in real implementation, this would update database
            updated_templates = []
            
            if update_data.get("welcome_mail"):
                updated_templates.append("welcome mail")
            if update_data.get("onboarding_mail"):
                updated_templates.append("onboarding mail")
            if update_data.get("consent_mail"):
                updated_templates.append("consent mail")

            logger.info(f"Combined emails updated for subadmin ID: {subadmin_id}")

            return {
                "subadmin_id": str(subadmin.id),
                "message": f"Successfully updated: {', '.join(updated_templates) if updated_templates else 'no templates'}",
                "success": True
            }
        except HTTPException as he:
            raise he
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to update combined emails: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update combined emails: {str(e)}"
            )

    async def get_all_subadmins(
        self,
        session: AsyncSession
    ) -> dict:
        try:
            # Get all subadmins without pagination
            query = select(Subadmin.id, Subadmin.name)
            result = await session.execute(query)
            subadmins = result.fetchall()

            # Format response
            subadmin_list = [
                {
                    "subadmin_id": str(subadmin.id),
                    "subadmin_name": subadmin.name or "Unnamed Subadmin"
                }
                for subadmin in subadmins
            ]

            logger.info(f"Retrieved {len(subadmin_list)} subadmins")

            return {
                "subadmins": subadmin_list,
                "success": True
            }
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to fetch subadmins: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch subadmins: {str(e)}"
            )
        
    