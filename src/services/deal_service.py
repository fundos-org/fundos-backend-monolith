from sqlmodel.ext.asyncio.session import AsyncSession
from ..models.deal import Deal
from ..schemas.deal import DealCreateRequest
from ..services.s3_services import S3Service

class DealService:
    @staticmethod
    async def create_deal(data: DealCreateRequest, db: AsyncSession, s3: S3Service) -> Deal:
        logo_url = s3.upload_file(data.logo) if data.logo else None
        pitch_deck_url = s3.upload_file(data.pitch_deck) if data.pitch_deck else None
        pitch_video_url = s3.upload_file(data.pitch_video) if data.pitch_video else None

        deal = Deal.model_validate(data.model_dump(exclude={"logo", "pitch_deck", "pitch_video"}))
        deal.logo_url = logo_url
        deal.pitch_deck_url = pitch_deck_url
        deal.pitch_video_url = pitch_video_url

        db.add(deal)
        await db.commit()
        await db.refresh(deal)
        return deal