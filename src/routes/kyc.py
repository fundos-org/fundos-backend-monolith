from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from typing import Annotated, Any
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from src.schemas.kyc import (
    AadhaarRequest, AadhaarResponse,
    SubmitOTPRequest, ResendOTPRequest,
    PanDetailsRequest, PanBankLinkRequest
)
from src.services.kyc import KycService
from src.services.phone import PhoneService
from src.services.user import UserService
from src.db.session import get_session

kyc_service = KycService()
phone_service = PhoneService()
user_service = UserService()

router = APIRouter()

@router.post('/aadhaar/otp/send')
async def verify_aadhaar(
    aadhaar_details: AadhaarRequest,
    session: Annotated[AsyncSession, Depends(get_session)]
) -> AadhaarResponse:
    try:
        response_data = await kyc_service.send_aadhaar_otp(
            user_id=aadhaar_details.user_id,
            aadhaar_number=aadhaar_details.aadhaar_number,
            session=session
        )
        content = AadhaarResponse(
            transaction_id=response_data["transaction_id"],
            fwdp=response_data["fwdp"],
            code_verifier=response_data["code_verifier"],
            message="OTP sent to Aadhaar registered mobile number"
        )
        return content
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send OTP: {str(e)}"
        )

@router.post('/aadhaar/otp/verify')
async def submit_aadhaar_otp(
    otp_details: SubmitOTPRequest,
    session: Annotated[AsyncSession, Depends(get_session)]
) -> dict:
    try:
        user_data = await kyc_service.submit_aadhaar_otp(
            user_id=otp_details.user_id,
            otp=otp_details.otp,
            session=session
        )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=dict(**user_data)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify OTP: {str(e)}"
        )

@router.post('/aadhaar/otp/resend')
async def resend_aadhaar_otp(
    otp_details: ResendOTPRequest,
    session: Annotated[AsyncSession, Depends(get_session)]
) -> dict:
    try:
        response_data = await kyc_service.resend_aadhaar_otp(
            unique_id=otp_details.user_id,
            aadhaar_number=otp_details.aadhaar_number,
            session=session
        )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=dict(**response_data)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resend OTP: {str(e)}"
        )

@router.post('/pan/verify')
async def verify_pan(
    pan_details: PanDetailsRequest,
    session: Annotated[AsyncSession, Depends(get_session)]
) -> dict:
    try:
        pan_data = await kyc_service.verify_pan(
            user_id=pan_details.user_id,
            pan_number=pan_details.pan_number,
            session=session
        )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=dict(**pan_data)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify PAN: {str(e)}"
        )

@router.post('/pan/bank/link/verify')
async def verify_pan_bank_link(
    pan_details: PanBankLinkRequest,
    session: Annotated[AsyncSession, Depends(get_session)]
) -> Any:  
    try:
        response = await kyc_service.verify_pan_bank_link(
            user_id=pan_details.user_id,
            pan_number=pan_details.pan_number,
            bank_account_number=pan_details.bank_account_number,
            ifsc_code=pan_details.ifsc_code,
            session=session
        )
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify PAN to Bank Account link: {str(e)}"
        )