from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.session import get_session
from typing import Optional, Dict, Annotated
from uuid import UUID
from src.services.bank import BankService
from src.models.user import User
from src.logging.logging_setup import get_logger

logger = get_logger(__name__)

router = APIRouter()

# Pydantic model for bank details input
class BankDetailsInput(BaseModel):
    user_id: UUID
    bank_account_number: str
    bank_ifsc: str
    account_holder_name: Optional[str] = None

@router.post("/initiate-verification")
async def initiate_bank_verification(
    bank_details: BankDetailsInput,
    session: Annotated[AsyncSession, Depends(get_session)]
):
    """
    Initiate bank account verification for the specified user.
    
    Args:
        bank_details: User ID, bank account number, IFSC, and optional account holder name.
        session: Database session.
    
    Returns:
        Dict with verification URL, request_id, and expiration.
    """
    try:
        bank_service = BankService()
        response = await bank_service.initiate_verification(
            user_id=bank_details.user_id,
            bank_details=bank_details.model_dump_json(exclude_unset=True),
            session=session
        )
        logger.info(f"Bank verification initiated for user_id: {bank_details.user_id}")
        return response
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error initiating verification for user_id {bank_details.user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to initiate verification")

@router.get("/check-status/{request_id}")
async def check_bank_status(
    request_id: str,
    user_id: UUID,
    session: AsyncSession = Depends(get_session)
):
    """
    Check the status of a bank verification request.
    
    Args:
        request_id: The request ID from initiate_verification.
        user_id: UUID of the user.
        session: Database session.
    
    Returns:
        Dict with transaction status and transaction ID.
    """
    try:
        bank_service = BankService()
        response = await bank_service.check_status(
            user_id=user_id,
            request_id=request_id,
            session=session
        )
        logger.info(f"Status checked for user_id: {user_id}, request_id: {request_id}")
        return response
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error checking status for user_id {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to check status")

@router.get("/retrieve-report/{txn_id}")
async def retrieve_bank_report(
    txn_id: str,
    user_id: UUID,
    session: AsyncSession = Depends(get_session)
):
    """
    Retrieve the bank verification report.
    
    Args:
        txn_id: The transaction ID from callback or status check.
        user_id: UUID of the user.
        session: Database session.
    
    Returns:
        Dict with verification details (e.g., beneficiary_name, is_name_match).
    """
    try:
        bank_service = BankService()
        response = await bank_service.retrieve_report(
            user_id=user_id,
            txn_id=txn_id,
            session=session
        )
        logger.info(f"Report retrieved for user_id: {user_id}, txn_id: {txn_id}")
        return response
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error retrieving report for user_id {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve report")

@router.post("/callback")
async def bank_webhook(
    data: Dict,
    session: AsyncSession = Depends(get_session)
):
    """
    Handle Digitap transaction completion webhook.
    
    Args:
        data: Callback data from Digitap.
        session: Database session.
    
    Returns:
        Dict acknowledging receipt.
    """
    try:
        bank_service = BankService()
        response = await bank_service.handle_callback(data=data, session=session)
        logger.info("Webhook processed successfully")
        return response
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process webhook")