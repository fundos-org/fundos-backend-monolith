from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from src.utils.dependencies import get_session
from src.schemas.payment import CreatePaymentReq, CreatePaymentRes, WebhookResponse
from src.services.payment import PaymentService
import os

router = APIRouter()

# Initialize PaymentService with environment variables
payment_service = PaymentService(
    api_key=os.getenv("PAYAID_API_KEY"),
    salt=os.getenv("PAYAID_SALT")
)

@router.post("/payments/create", response_model=CreatePaymentRes)
async def create_payment(
    session: Annotated[AsyncSession, Depends(get_session)],
    data: CreatePaymentReq
) -> CreatePaymentRes:
    """
    Create a payment request for an investment and return a payment URL for the mobile app.
    """
    try:
        payment_url = await payment_service.create_payment(
            session=session,
            investment_id=data.investment_id,
            amount=data.amount,
            customer_name=data.customer_name,
            customer_email=data.customer_email,
            customer_phone=data.customer_phone,
            description=data.description,
            currency=data.currency,
            expiry_in_minutes=data.expiry_in_minutes
        )
        return CreatePaymentRes(success=True, data=payment_url)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create payment: {str(e)}")

@router.post("/webhook/payaid", response_model=WebhookResponse)
async def handle_payaid_webhook(
    session: Annotated[AsyncSession, Depends(get_session)],
    data: dict
) -> WebhookResponse:
    """
    Handle Payaid webhook callbacks to update investment payment status.
    """
    try:
        await payment_service.handle_webhook(session=session, webhook_data=data)
        return WebhookResponse(success=True, message="Webhook processed successfully")
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process webhook: {str(e)}")