from src.services.payments.benepay import PaymentService
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.utils.dependencies import get_session
from typing import Dict, Any, Annotated
from src.logging.logging_setup import get_logger  
from src.schemas.v2.payment import PaymentWebhookData, PaymentRequestData  

logger = get_logger(__name__)

router = APIRouter()
payment_service = PaymentService()

@router.post("/create/url")
async def create_payment(
    data: PaymentRequestData, 
    session: Annotated[AsyncSession, Depends(get_session)]
)-> Dict[str, Any]:
    logger.info(f"Received data: {data}")

    response = await payment_service.send_payment_url(
        data=data, 
        session=session
    )
    return response

@router.post("/handle/webhook")
async def handle_payment_webhook(
    data: PaymentWebhookData
) -> Dict[str, Any]:
    logger.info(f"Received data: {data}")
    
    response = await payment_service.handle_webhook(data)
    return response