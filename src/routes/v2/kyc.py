from typing import Annotated, Any, Dict
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.session import get_session
from src.services.ukyc import UnifiedKycService

router = APIRouter() 
kyc_service = UnifiedKycService()

@router.post("/generate-url")
async def generate_kyc_url(
    user_id: str, 
    session: Annotated[AsyncSession, Depends(get_session)]
)-> Dict[str, Any]:
    
    response = await kyc_service.send_kyc_request(
        user_id=user_id,
        session=session
    )

    return response

@router.get("/details")
async def verify_kyc(
    user_id: str, 
    session: Annotated[AsyncSession, Depends(get_session)]
) -> Dict[str, Any]:
    response = await kyc_service.get_kyc_details(
        user_id=user_id,
        session=session
    )

    return response