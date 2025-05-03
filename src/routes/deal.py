from fastapi import APIRouter, Depends, Form
from uuid import UUID
from sqlmodel.ext.asyncio.session import AsyncSession
from starlette import status

from src.schemas.deal import DealCreateRequest, DealCreateResponse
from src.utils.dependencies import get_s3_service
from src.db.session import get_session
from src.services.s3 import S3Service
from src.services.deal import DealService
from src.utils.json_response import success_response, error_response

router = APIRouter()

@router.post("/create/draft")
async def create_deal_draft(
    fund_manager_id: int = Form(...),
    db: AsyncSession = Depends(get_session)
):
    try:
        deal = await DealService.create_draft(fund_manager_id, db)
        response_data = DealCreateResponse.model_validate(deal)
        return success_response("Deal draft created", response_data.model_dump(), status.HTTP_201_CREATED)
    except Exception as e:
        return error_response(f"Failed to create deal draft: {str(e)}", status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.patch("/update/{deal_id}")
async def update_deal(
    deal_id: UUID,
    form_data: DealCreateRequest = Depends(),
    db: AsyncSession = Depends(get_session),
    s3: S3Service = Depends(get_s3_service)
):
    try:
        deal = await DealService.update_deal_partial(deal_id, form_data, db, s3)
        response_data = DealCreateResponse.model_validate(deal)
        return success_response("Deal updated successfully", response_data.model_dump())
    except Exception as e:
        return error_response(f"Failed to update deal: {str(e)}", status.HTTP_500_INTERNAL_SERVER_ERROR)
