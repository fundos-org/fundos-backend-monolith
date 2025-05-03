import datetime
from fastapi import HTTPException
from sqlmodel import UUID
from sqlmodel.ext.asyncio.session import AsyncSession
from src.models.deal import Deal
from src.schemas.deal import DealCreateRequest
from src.services.s3 import S3Service
from src.utils.dependencies import get_session

class DealService:
    def __init__(self):
        self.session = get_session()


    @staticmethod
    async def create_draft(self, fund_manager_id: int) -> Deal:
        deal_row = Deal(fund_manager_id=fund_manager_id)
        await self.session.add(deal_row)
        await self.session.commit()
        await self.session.refresh(deal_row)
        return deal_row

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
