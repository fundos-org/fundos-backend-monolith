from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from starlette import status
from schemas.deal import DealCreateRequest, DealCreateResponse
from sqlmodel.ext.asyncio.session import AsyncSession 
from utils.dependencies import get_db, get_s3_service
from services.s3_services import S3Service
from services.deal_service import DealService

router = APIRouter() 

@router.get('/')
def deals_root():
    content = {"isSuccess": True, "message": "deals route hit successfully"}
    return JSONResponse(status_code=status.HTTP_200_OK, content=content)


@router.post("/create-deal", response_model=DealCreateResponse)
async def create_deal(
    form_data: DealCreateRequest = Depends(),
    db: AsyncSession = Depends(get_db),
    s3: S3Service = Depends(get_s3_service)
):
    deal = await DealService.create_deal(form_data, db, s3)
    return deal