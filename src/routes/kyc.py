from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from src.schemas.kyc import (
    AadhaarRequest, AadhaarResponse,
    SubmitOTPRequest, ResendOTPRequest,
    PanDetailsRequest
)
from src.schemas.kyc_validation import (
    ValidateAadhaarRequest, ValidatePanRequest,
    PanAadhaarLinkRequest
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

@router.post('/aadhaar/otp/verify', tags=["aadhaar"])
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

@router.post('/aadhaar/otp/resend', tags=["aadhaar"])
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

@router.post("/aadhaar/validate", tags=["aadhaar"])
async def validate_aadhaar(
    validation_details: ValidateAadhaarRequest,
    session: Annotated[AsyncSession, Depends(get_session)]
) -> dict:
    try:
        response_data = await kyc_service.validate_aadhaar(
            client_ref_num=validation_details.client_ref_num,
            aadhaar_number=validation_details.aadhaar_number,
            session=session
        )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=dict(**response_data)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate Aadhaar: {str(e)}"
        )

@router.post('/pan/verify', tags=["pan"])
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

@router.post("/pan/validate", tags=["pan"])
async def validate_pan(
    validation_details: ValidatePanRequest,
    session: Annotated[AsyncSession, Depends(get_session)]
) -> dict:
    try:
        response_data = await kyc_service.validate_pan(
            client_ref_num=validation_details.client_ref_num,
            pan_number=validation_details.pan_number,
            full_name=validation_details.full_name,
            session=session
        )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=dict(**response_data)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate PAN: {str(e)}"
        )

@router.post("/pan/aadhaar/link", tags=["pan", "aadhaar"])
async def validate_pan_aadhaar_linked(
    validation_details: PanAadhaarLinkRequest,
    session: Annotated[AsyncSession, Depends(get_session)]
) -> dict:
    try:
        response_data = await kyc_service.validate_pan_aadhaar_link(
            client_ref_num=validation_details.client_ref_num,
            pan_number=validation_details.pan_number,
            aadhaar_number=validation_details.aadhaar_number,
            session=session
        )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=dict(**response_data)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate PAN-Aadhaar link: {str(e)}"
        )