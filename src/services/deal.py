import datetime
from fastapi import HTTPException
from sqlmodel import UUID
from sqlmodel.ext.asyncio.session import AsyncSession
from src.models.deal import Deal
from src.schemas.deal import DealCreateRequest
from services.s3 import S3Service

class DealService:
    @staticmethod
    async def create_draft(fund_manager_id: int, db: AsyncSession) -> Deal:
        deal = Deal(fund_manager_id=fund_manager_id)
        db.add(deal)
        await db.commit()
        await db.refresh(deal)
        return deal

    @staticmethod
    async def update_deal_partial(
        deal_id: UUID, 
        data: DealCreateRequest, 
        db: AsyncSession, 
        s3: S3Service
    ) -> Deal:
        deal = await db.get(Deal, deal_id)
        if not deal:
            raise HTTPException(status_code=404, detail="Deal not found")

        update_data = data.model_dump(exclude_unset=True, exclude={"logo", "pitch_deck", "pitch_video"})

        # Upload files if provided
        if data.logo:
            deal.logo_url = s3.upload_file(data.logo)
        if data.pitch_deck:
            deal.pitch_deck_url = s3.upload_file(data.pitch_deck)
        if data.pitch_video:
            deal.pitch_video_url = s3.upload_file(data.pitch_video)

        for key, value in update_data.items():
            setattr(deal, key, value)

        deal.updated_at = datetime.now(datetime.timezone.utc)

        await db.commit()
        await db.refresh(deal)
        return deal
