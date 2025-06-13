from datetime import datetime
from fastapi import HTTPException, UploadFile, BackgroundTasks
from typing import Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.models.subadmin import Subadmin
from src.models.user import User
from src.logging.logging_setup import get_logger
from sqlmodel import UUID
from src.models.deal import Deal, DealStatus, BusinessModel, CompanyStage, TargetCustomerSegment, InstrumentType
from src.services.s3 import S3Service
from src.utils.dependencies import get_deal
from src.configs.configs import aws_config, redis_configs
import redis.asyncio as redis
import json
import uuid
import mimetypes

logger = get_logger(__name__)
REDIS_HOST = redis_configs.redis_host 
REDIS_PORT = redis_configs.redis_port
REDIS_DB = redis_configs.redis_db
CACHE_TTL = redis_configs.redis_cache_ttl  # 7 days for Zoho metadata

class DealService:
    def __init__(self):
        self.bucket_name = aws_config.aws_bucket
        self.folder_prefix = aws_config.aws_deals_folder
        self.s3_service = S3Service(bucket_name=self.bucket_name, region_name=aws_config.aws_region)
        self.redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True
        )

    async def _cache_deal_data(self, deal_id: UUID, data: Dict):
        """Cache deal data in Redis with a TTL of 24 hours."""
        try:
            await self.redis_client.setex(
                f"deal:{deal_id}", 
                86400,  # 24 hours TTL
                json.dumps(data, default=str)
            )
        except Exception as e:
            logger.error(f"Failed to cache deal data: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to cache deal data")

    async def _get_cached_deal_data(self, deal_id: UUID) -> Dict:
        """Retrieve deal data from Redis."""
        try:
            cached_data = await self.redis_client.get(f"deal:{deal_id}")
            if not cached_data:
                raise HTTPException(status_code=404, detail="Deal not found in cache")
            return json.loads(cached_data)
        except Exception as e:
            logger.error(f"Failed to retrieve cached deal data: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to retrieve cached deal data")

    async def _upload_file_background(
        self, 
        background_tasks: BackgroundTasks, 
        object_id: UUID, 
        file: UploadFile, 
        folder_prefix: str
    ) -> str:
        """Schedule S3 file upload as a background task and return object key."""
        try:
            file_content = await file.read()
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            file_extension = mimetypes.guess_extension(file.content_type) or '.jpg'
            object_name = f"{folder_prefix}{object_id}_{timestamp}{file_extension}"

            # Track upload status in Redis
            await self.redis_client.setex(
                f"upload:{object_name}", 
                86400,  # Same TTL as deal data
                "pending"
            )

            # Schedule background upload
            background_tasks.add_task(
                self.s3_service.background_upload_file,
                file_content=file_content,
                object_name=object_name,
                content_type=file.content_type
            )
            return object_name
        except Exception as e:
            logger.error(f"Failed to schedule file upload: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to schedule file upload")

    async def _check_upload_status(self, object_key: str) -> bool:
        """Check if an S3 upload is complete."""
        status = await self.redis_client.get(f"upload:{object_key}")
        if status != "completed":
            logger.warning(f"Upload not completed for {object_key}, status: {status}")
            return False
        return True

    async def create_draft(
        self, 
        fund_manager_id: UUID, 
        session: AsyncSession
    ) -> Dict:
        """
        Creates a new deal draft and stores it in Redis.

        Args:
            fund_manager_id: ID of the fund manager creating the deal
            session: SQLAlchemy AsyncSession for database operations

        Returns:
            Dict: The created deal data

        Raises:
            HTTPException: If there's an error during creation
        """
        try:
            deal_id = uuid.uuid4()
            deal_data = {
                "id": str(deal_id),
                "fund_manager_id": str(fund_manager_id),
                "status": DealStatus.ON_HOLD.value,
            }
            await self._cache_deal_data(deal_id, deal_data)
            return deal_data
        except Exception as e:
            logger.error(f"Failed to create deal draft: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")

    async def update_company_details(
        self, 
        deal_id: UUID, 
        logo: UploadFile, 
        company_name: str, 
        about_company: str, 
        company_website: str,
        session: AsyncSession,
        background_tasks: BackgroundTasks
    ) -> Dict:
        """
        Updates the company details for a deal in Redis.

        Args:
            deal_id: UUID of the deal to update
            logo: Company logo
            company_name: Name of the company
            about_company: Description of the company
            company_website: Website URL of the company
            session: SQLAlchemy AsyncSession for database operations
            background_tasks: FastAPI BackgroundTasks for async operations

        Returns:
            Dict: Updated deal data

        Raises:
            HTTPException: If deal not found or update fails
        """
        try:
            deal_data = await self._get_cached_deal_data(deal_id)
            logo_key = await self._upload_file_background(
                background_tasks=background_tasks,
                object_id=deal_id,
                file=logo,
                folder_prefix=f"{self.folder_prefix}/logos/"
            )
            deal_data.update({
                "company_name": company_name,
                "about_company": about_company,
                "company_website": company_website,
                "logo_key": logo_key
            })
            await self._cache_deal_data(deal_id, deal_data)
            return deal_data
        except HTTPException as he:
            raise he
        except Exception as e:
            logger.error(f"Failed to update company details: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")

    async def update_industry_problem(
        self, 
        deal_id: UUID, 
        industry: str, 
        problem_statement: str, 
        business_model: str, 
        session: AsyncSession
    ) -> Dict:
        """
        Updates industry, problem statement, and business model for a deal in Redis.

        Args:
            deal_id: UUID of the deal to update
            industry: Industry of the company
            problem_statement: Problem statement the company addresses
            business_model: Business model of the company
            session: SQLAlchemy AsyncSession for database operations

        Returns:
            Dict: Updated deal data

        Raises:
            HTTPException: If deal not found or update fails
        """
        try:
            deal_data = await self._get_cached_deal_data(deal_id)
            if business_model not in [e.value for e in BusinessModel]:
                raise HTTPException(status_code=400, detail=f"Invalid business_model: {business_model}")
            deal_data.update({
                "industry": industry,
                "problem_statement": problem_statement,
                "business_model": business_model,
            })
            await self._cache_deal_data(deal_id, deal_data)
            return deal_data
        except HTTPException as he:
            raise he
        except Exception as e:
            logger.error(f"Failed to update industry and problem details: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")

    async def update_customer_segment(
        self, 
        deal_id: UUID, 
        target_customer_segment: str, 
        company_stage: str,
        session: AsyncSession
    ) -> Dict:
        """
        Updates customer segment details for a deal in Redis.

        Args:
            deal_id: UUID of the deal to update
            target_customer_segment: Target customer segment
            company_stage: Stage of the company
            session: SQLAlchemy AsyncSession for database operations

        Returns:
            Dict: Updated deal data

        Raises:
            HTTPException: If deal not found or update fails
        """
        try:
            deal_data = await self._get_cached_deal_data(deal_id)
            if target_customer_segment not in [e.value for e in TargetCustomerSegment]:
                raise HTTPException(status_code=400, detail=f"Invalid target_customer_segment: {target_customer_segment}")
            if company_stage not in [e.value for e in CompanyStage]:
                raise HTTPException(status_code=400, detail=f"Invalid company_stage: {company_stage}")
            deal_data.update({
                "target_customer_segment": target_customer_segment,
                "company_stage": company_stage,
            })
            await self._cache_deal_data(deal_id, deal_data)
            return deal_data
        except HTTPException as he:
            raise he
        except Exception as e:
            logger.error(f"Failed to update customer segment: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")

    async def update_valuation(
        self,
        deal_id: UUID,
        current_valuation: float,
        round_size: float,
        syndicate_commitment: float,
        pitch_deck: UploadFile,
        pitch_video: UploadFile, 
        investment_scheme_appendix: UploadFile,
        session: AsyncSession,
        background_tasks: BackgroundTasks
    ) -> Dict:
        """
        Updates valuation details for a deal in Redis.

        Args:
            deal_id: UUID of the deal to update
            current_valuation: Current valuation of the company
            round_size: Size of the funding round
            syndicate_commitment: Syndicate's commitment amount
            pitch_deck: Pitch deck file
            pitch_video: Pitch video file
            session: SQLAlchemy AsyncSession for database operations
            background_tasks: FastAPI BackgroundTasks for async operations

        Returns:
            Dict: Updated deal data

        Raises:
            HTTPException: If deal not found or update fails
        """
        try:
            deal_data = await self._get_cached_deal_data(deal_id)
            pitch_deck_key = await self._upload_file_background(
                background_tasks=background_tasks,
                object_id=deal_id,
                file=pitch_deck,
                folder_prefix=f"{self.folder_prefix}/pitch_decks/"
            )
            pitch_video_key = await self._upload_file_background(
                background_tasks=background_tasks,
                object_id=deal_id,
                file=pitch_video,
                folder_prefix=f"{self.folder_prefix}/pitch_videos/"
            )
            investment_scheme_appendix_key = await self._upload_file_background(
                background_tasks=background_tasks, 
                object_id=deal_id, 
                file=investment_scheme_appendix, 
                folder_prefix=f"{self.folder_prefix}/investment_scheme_appendix/"
            )

            deal_data.update({
                "current_valuation": current_valuation,
                "round_size": round_size,
                "syndicate_commitment": syndicate_commitment,
                "pitch_deck_key": pitch_deck_key,
                "pitch_video_key": pitch_video_key,
                "investment_scheme_appendix_key" : investment_scheme_appendix_key
            })
            await self._cache_deal_data(deal_id, deal_data)
            return deal_data
        except HTTPException as he:
            raise he
        except Exception as e:
            logger.error(f"Failed to update valuation details: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")

    async def update_securities(
        self,
        deal_id: UUID,
        instrument_type: str,
        conversion_terms: str,
        is_startup: bool,
        management_fee: float, 
        carry: float,
        session: AsyncSession
    ) -> Deal:
        """
        Updates securities details for a deal and persists to database.

        Args:
            deal_id: UUID of the deal to update
            instrument_type: Type of financial instrument
            conversion_terms: Terms for conversion
            is_startup: Whether the company is a startup
            session: SQLAlchemy AsyncSession for database operations

        Returns:
            Deal: Updated database deal object

        Raises:
            HTTPException: If deal not found or update fails
        """
        try:
            deal_data = await self._get_cached_deal_data(deal_id)
            if instrument_type not in [e.value for e in InstrumentType]:
                raise HTTPException(status_code=400, detail=f"Invalid instrument_type: {instrument_type}")

            deal_data.update({
                "instrument_type": instrument_type,
                "conversion_terms": conversion_terms,
                "agreed_to_terms": is_startup,
                "management_fee": management_fee, 
                "carry": carry
            })

            try:
                deal = Deal(
                    id=uuid.UUID(deal_data["id"]),
                    fund_manager_id=uuid.UUID(deal_data["fund_manager_id"]),
                    status=DealStatus(deal_data.get("status", DealStatus.OPEN.value)),
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    company_name=deal_data.get("company_name"),
                    about_company=deal_data.get("about_company"),
                    company_website=deal_data.get("company_website"),
                    logo_url=deal_data.get("logo_key"),
                    industry=deal_data.get("industry"),
                    problem_statement=deal_data.get("problem_statement"),
                    business_model=BusinessModel(deal_data["business_model"]) if deal_data.get("business_model") else None,
                    company_stage=CompanyStage(deal_data["company_stage"]) if deal_data.get("company_stage") else None,
                    target_customer_segment=TargetCustomerSegment(deal_data["target_customer_segment"]) if deal_data.get("target_customer_segment") else None,
                    current_valuation=float(deal_data["current_valuation"]) if deal_data.get("current_valuation") else None,
                    round_size=float(deal_data["round_size"]) if deal_data.get("round_size") else None,
                    syndicate_commitment=float(deal_data["syndicate_commitment"]) if deal_data.get("syndicate_commitment") else None,
                    pitch_deck_url=deal_data.get("pitch_deck_key"),
                    pitch_video_url=deal_data.get("pitch_video_key"),
                    investment_appendix_key=deal_data.get("investment_scheme_appendix_key"),
                    instrument_type=InstrumentType(deal_data["instrument_type"]) if deal_data.get("instrument_type") else None,
                    conversion_terms=deal_data.get("conversion_terms"),
                    agreed_to_terms=bool(deal_data["agreed_to_terms"]) if deal_data.get("agreed_to_terms") is not None else False,
                    investment_appendix_uploaded=True,
                    management_fee=float(deal_data.get("management_fee")),
                    carry=float(deal_data.get("carry"))
                )
            except ValueError as ve:
                logger.error(f"Type conversion error: {str(ve)}")
                raise HTTPException(status_code=400, detail=f"Invalid data type: {str(ve)}")

            session.add(deal)
            await session.commit()
            await session.refresh(deal)

            # Clean up Redis cache
            await self.redis_client.delete(f"deal:{deal_id}")
            for key in [deal_data.get("logo_key"), deal_data.get("pitch_deck_key"), deal_data.get("pitch_video_key")]:
                if key:
                    await self.redis_client.delete(f"upload:{key}")

            return deal
        except ValueError as ve:
            logger.error(f"Invalid UUID: {str(ve)}")
            raise HTTPException(status_code=400, detail="Invalid UUID format for deal_id")
        except HTTPException as he:
            raise he
        except Exception as e:
            logger.error(f"Failed to update securities details: {str(e)}")
            await session.rollback()
            raise HTTPException(status_code=500, detail="Internal server error")

    async def get_deal_by_id(
        self, 
        deal_id: UUID, 
        session: AsyncSession
    ) -> Dict:
        """
        Retrieves a deal by its ID from cache or database.

        Args:
            deal_id: UUID of the deal to retrieve
            session: SQLAlchemy AsyncSession for database operations

        Returns:
            Dict: Deal data

        Raises:
            HTTPException: If deal not found or retrieval fails
        """
        try:

            deal = await session.get(Deal, deal_id)
            if not deal:
                raise HTTPException(status_code=404, detail="Deal not found")
            
            deal_data = {
                "deal_id": str(deal.id),
                "description": deal.about_company,  
                "title": deal.company_name, 
                "current_valuation": deal.current_valuation,
                "round_size": deal.round_size,
                "minimum_investment": "5L",
                "commitment": deal.syndicate_commitment,
                "business_model": deal.business_model,
                "company_stage": deal.company_stage,
                "instruments": deal.instrument_type,
                "valuation_type": "Priced",
                "fund_raised_till_now": 0,
                "logo_url": deal.logo_url,
            }
            return deal_data
        except HTTPException as he:
            raise he
        except Exception as e:
            logger.error(f"Failed to retrieve deal by ID: {str(e)}")
            await session.rollback()
            raise HTTPException(status_code=500, detail="Internal server error")

    async def get_deals_by_user_id(
        self, 
        user_id: UUID,  
        session: AsyncSession
    ) -> Dict:
        """
        Retrieves deals by user ID from the database.

        Args:
            user_id: UUID of the user
            session: SQLAlchemy AsyncSession for database operations

        Returns:
            Dict: Containing subadmin and deal details

        Raises:
            HTTPException: If retrieval fails
        """
        try:
            # Fetch user details
            statement = select(User).where(User.id == user_id)
            result = await session.execute(statement)
            user = result.scalars().one()

            # Subadmin details
            subadmin_id = user.fund_manager_id

            # Fetch deals
            statement = select(Deal).where(Deal.fund_manager_id == subadmin_id)
            result = await session.execute(statement)
            deals = result.scalars().all()

            # Fetch subadmin details
            statement = select(Subadmin).where(Subadmin.id == subadmin_id)
            result = await session.execute(statement)
            subadmin = result.scalars().one()

            # Prepare response
            response = {
                "subadmin_name": subadmin.name,
                "user_name": f"{user.first_name} {user.last_name}",
                "subadmin_id": str(subadmin_id)
            }

            # Prepare deals data
            deals_data = []
            for deal in deals:
                deal_data = {
                    "deal_id": str(deal.id),
                    "description": deal.about_company,
                    "title": deal.company_name,
                    "deal_status": deal.status,
                    "current_valuation": deal.current_valuation,
                    "round_size": deal.round_size,
                    "commitment": deal.syndicate_commitment,
                    "business_model": deal.business_model,
                    "company_stage": deal.company_stage,
                    "logo_url": deal.logo_url,
                    "created_at": deal.created_at
                }
                deals_data.append(deal_data)

            response["deals_data"] = deals_data
            return response
        
        except Exception as e:
            logger.error(f"Failed to retrieve deals by User ID: {str(e)}")
            await session.rollback()
            raise HTTPException(status_code=500, detail="Internal server error")