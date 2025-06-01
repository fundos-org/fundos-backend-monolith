from datetime import datetime
from fastapi import HTTPException, UploadFile
from typing import Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.models.subadmin import Subadmin
from src.logging.logging_setup import get_logger
from sqlmodel import UUID
from src.models.deal import Deal, DealStatus
from src.services.s3 import S3Service
from src.utils.dependencies import get_deal

logger = get_logger(__name__)

class DealService:
    def __init__(self):
        self.bucket_name = "fundos-dev-bucket"
        self.folder_prefix = "deals"
        self.s3_service = S3Service(bucket_name=self.bucket_name, region_name="ap-south-1")

    async def create_draft(
        self, 
        fund_manager_id: UUID, 
        session: AsyncSession
    ) -> Deal:
        """
        Creates a new deal draft for a fund manager.

        Args:
            fund_manager_id: ID of the fund manager creating the deal
            db: SQLAlchemy AsyncSession for database operations

        Returns:
            Deal: The created deal object

        Raises:
            HTTPException: If there's an error during creation
        """
        try:
            deal_row = Deal(
                fund_manager_id=fund_manager_id,
                title="New Deal Draft",
                description="Draft deal created", 
                status= DealStatus.OPEN, 
                created_at=datetime.now()
            )
            session.add(deal_row)
            await session.commit()
            await session.refresh(deal_row)
            return deal_row

        except Exception as e:
            logger.error(f"Failed to create deal draft: {str(e)}")
            await session.rollback()
            raise HTTPException(status_code=500, detail="Internal server error")

    async def update_company_details(
        self, 
        deal_id: UUID, 
        logo: UploadFile, 
        company_name: str, 
        about_company: str, 
        company_website: str,
        session: AsyncSession
    ) -> Deal:
        """
        Updates the company details for a deal.

        Args:
            deal_id: UUID of the deal to update
            company_name: Name of the company
            about_company: Description of the company
            company_website: Website URL of the company
            session: SQLAlchemy AsyncSession for database operations

        Returns:
            Deal: Updated deal object

        Raises:
            HTTPException: If deal not found or update fails
        """
        try:
            deal = await get_deal(deal_id = deal_id, session = session)
            if not deal:
                raise HTTPException(status_code=404, detail="Deal not found")

            deal.company_name = company_name
            deal.about_company = about_company
            deal.company_website = company_website
            deal.logo_url = await self.s3_service.upload_and_get_url(
                object_id=deal_id,
                file=logo,
                bucket_name=f"{self.bucket_name}",
                folder_prefix=f"{self.folder_prefix}/logos/",
            )
            deal.updated_at = datetime.now()

            await session.commit()
            await session.refresh(deal)
            return deal

        except HTTPException as he:
            raise he
        except Exception as e:
            logger.error(f"Failed to update company details: {str(e)}")
            await session.rollback()
            raise HTTPException(status_code=500, detail="Internal server error")

    async def update_industry_problem(
        self, 
        deal_id: UUID, 
        industry: str, 
        problem_statement: str, 
        business_model: str, 
        session: AsyncSession
    ) -> Deal:
        """
        Updates industry, problem statement, and business model for a deal.

        Args:
            deal_id: UUID of the deal to update
            industry: Industry of the company
            problem_statement: Problem statement the company addresses
            business_model: Business model of the company
            session: SQLAlchemy AsyncSession for database operations

        Returns:
            Deal: Updated deal object

        Raises:
            HTTPException: If deal not found or update fails
        """
        try:
            deal = await get_deal(deal_id = deal_id, session = session)
            if not deal:
                raise HTTPException(status_code=404, detail="Deal not found")

            deal.industry = industry
            deal.problem_statement = problem_statement
            deal.business_model = business_model
            deal.updated_at = datetime.now()

            await session.commit()
            await session.refresh(deal)
            return deal

        except HTTPException as he:
            raise he
        except Exception as e:
            logger.error(f"Failed to update industry and problem details: {str(e)}")
            await session.rollback()
            raise HTTPException(status_code=500, detail="Internal server error")

    async def update_customer_segment(
        self, 
        deal_id: UUID, 
        target_customer_segment: str, 
        company_stage: str, 
        session: AsyncSession
    ) -> Deal:
        """
        Updates customer segment details for a deal.

        Args:
            deal_id: UUID of the deal to update
            target_customer_segment: Target customer segment
            customer_segment_type: Type of customer segment
            session: SQLAlchemy AsyncSession for database operations

        Returns:
            Deal: Updated deal object

        Raises:
            HTTPException: If deal not found or update fails
        """
        try:
            deal = await get_deal(deal_id = deal_id, session = session)
            if not deal:
                raise HTTPException(status_code=404, detail="Deal not found")

            deal.target_customer_segment = target_customer_segment
            deal.company_stage = company_stage
            deal.updated_at = datetime.now()

            await session.commit()
            await session.refresh(deal)
            return deal

        except HTTPException as he:
            raise he
        except Exception as e:
            logger.error(f"Failed to update customer segment: {str(e)}")
            await session.rollback()
            raise HTTPException(status_code=500, detail="Internal server error")

    async def update_valuation(
        self,
        deal_id: UUID,
        current_valuation: float,
        round_size: float,
        syndicate_commitment: float,
        pitch_deck: UploadFile,
        pitch_video: UploadFile, 
        session: AsyncSession
    ) -> Deal:
        """
        Updates valuation details for a deal.

        Args:
            deal_id: UUID of the deal to update
            current_valuation: Current valuation of the company
            round_size: Size of the funding round
            syndicate_commitment: Syndicate's commitment amount
            session: SQLAlchemy AsyncSession for database operations

        Returns:
            Deal: Updated deal object

        Raises:
            HTTPException: If deal not found or update fails
        """
        try:
            deal = await get_deal(deal_id = deal_id, session = session)
            if not deal:
                raise HTTPException(status_code=404, detail="Deal not found")

            deal.current_valuation = current_valuation
            deal.round_size = round_size
            deal.syndicate_commitment = syndicate_commitment
            deal.pitch_deck_url = await self.s3_service.upload_and_get_url(
                object_id=deal_id,
                file=pitch_deck,
                bucket_name=self.bucket_name,
                folder_prefix=f"{self.folder_prefix}/pitch_decks/"
            )
            deal.pitch_video_url = await self.s3_service.upload_and_get_url(
                object_id=deal_id,
                file=pitch_video, 
                bucket_name=self.bucket_name,
                folder_prefix=f"{self.folder_prefix}/pitch_videos/"
            )
            deal.updated_at = datetime.now()

            await session.commit()
            await session.refresh(deal)
            return deal

        except HTTPException as he:
            raise he
        except Exception as e:
            logger.error(f"Failed to update valuation details: {str(e)}")
            await session.rollback()
            raise HTTPException(status_code=500, detail="Internal server error")

    async def update_securities(
        self,
        deal_id: UUID,
        instrument_type: str,
        conversion_terms: str,
        is_startup: bool,
        session: AsyncSession
    ) -> Deal:
        """
        Updates securities details for a deal.

        Args:
            deal_id: UUID of the deal to update
            instrument_type: Type of financial instrument
            conversion_terms: Terms for conversion
            is_startup: Whether the company is a startup
            session: SQLAlchemy AsyncSession for database operations

        Returns:
            Deal: Updated deal object

        Raises:
            HTTPException: If deal not found or update fails
        """
        try:
            deal = await get_deal(deal_id=deal_id, session=session)
            if not deal:
                raise HTTPException(status_code=404, detail="Deal not found")

            deal.instrument_type = instrument_type
            deal.conversion_terms = conversion_terms
            deal.agreed_to_terms = is_startup
            deal.updated_at = datetime.now()

            await session.commit()
            await session.refresh(deal)
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
    ) -> Any:
        """
        Retrieves a deal by its ID.

        Args:
            deal_id: UUID of the deal to retrieve
            session: SQLAlchemy AsyncSession for database operations

        Returns:
            Deal: The requested deal object

        Raises:
            HTTPException: If deal is not found or retrieval fails
        """
        try:
            deal = await get_deal(deal_id=deal_id, session=session)
            if not deal:
                raise HTTPException(status_code=404, detail="Deal not found")
            
            deal_data = {
                "deal_id": deal.id,
                "description": deal.about_company,  
                "title": deal.company_name, 
                "current_valuation": deal.current_valuation,
                "round_size": deal.round_size,
                "minimum_investment": "5L",
                "commitment": deal.syndicate_commitment,
                "instruments": deal.instrument_type,
                "valuation_type": "Priced",
                "fund_raised_till_now": 0,
                "logo_url": deal.logo_url,
                "fund_manager_id": deal.fund_manager_id,
            }
            return deal_data
        except HTTPException as he:
            raise he
        except Exception as e:
            logger.error(f"Failed to retrieve deal by ID: {str(e)}")
            await session.rollback()
            raise HTTPException(status_code=500, detail="Internal server error")

    async def get_deals_by_subadmin_id(
        self, 
        subadmin_id: UUID, 
        session: AsyncSession
    ) -> Any: 
        try:
            statement = select(Deal).where(Deal.fund_manager_id == subadmin_id)
            results = await session.execute(statement)
            deals = results.scalars().all()

            # fetch subadmin details
            statement = select(Subadmin).where(Subadmin.id == subadmin_id)
            results = await session.execute(statement)
            subadmin = results.scalars().one()

            response: Dict = {
                "subadmin_name": subadmin.name,
            }

            # Prepare response
            deals_data = []
            for deal in deals:
                deal_data = {
                    "deal_id": deal.id,
                    "description": deal.about_company,  
                    "title": deal.company_name, 
                    "current_valuation": deal.current_valuation,
                    "round_size": deal.round_size,
                    "commitment": deal.syndicate_commitment,
                    "logo_url": deal.logo_url,
                    "fund_manager_id": deal.fund_manager_id,
                    "fund_manager_name": subadmin.name
                }
                deals_data.append(deal_data)

            response["deals_data"] = deals_data
            return response
        
        except Exception as e:
            logger.error(f"Failed to retrieve deals by subadmin ID: {str(e)}")
            await session.rollback()
            raise HTTPException(status_code=500, detail="Internal server error")
        except HTTPException as he:
            raise he
