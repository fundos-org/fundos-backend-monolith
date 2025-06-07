from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from starlette import status
from pydantic import EmailStr
from src.logging.logging_setup import get_logger
from src.db.session import get_session 
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated, Dict, Any, Optional
from src.schemas.kyc import (EmailVerifyOtpRequest, EmailVerifyOtpResponse, AgreementRequest, AgreementResponse, 
                            DeclarationRequest, DeclarationResponse, ChooseInvestorRequest, ChooseInvestorResponse, 
                            PhoneNumSendOtpRequest, EmailSendOtpRequest, EmailSendOtpResponse, PhoneNumSendOtpResponse, 
                            PhoneNumVerifyOtpRequest, PhoneNumVerifyOtpResponse, UserDetailsRequest, UserDetailsResponse, 
                            ProfessionalBackgroundRequest, ProfessionalBackgroundResponse, PhotoUploadRequest, PhotoUploadResponse
                            , UserOnboardingStartResponse, UserOnboardingStartRequest)
from src.services.dummy import DummyService
from src.services.email import EmailService 
from src.services.zoho import ZohoService

router = APIRouter() 

# service initialization 
dummy_service = DummyService()
email_service = EmailService()
zoho_service = ZohoService()

logger = get_logger(__name__)

@router.get("/user/phone/otp/send")
async def user_send_phone_otp(
    session: Annotated[AsyncSession, Depends(get_session)], 
    phone_number: str, 
    invite_code: Optional[str] = None
) -> Dict[str, Any]:

    result = await dummy_service.send_phone_otp(
        session=session,
        phone_number=phone_number, 
        invite_code=invite_code
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=f"{result['message']}")

    return result

@router.get("/user/phone/otp/verify")
async def user_verify_phone_otp(
    session: Annotated[AsyncSession, Depends(get_session)], 
    phone_number: str,
    otp: str, 
    invite_code: Optional[str] = None
) -> Dict[str, Any]:

    result = await dummy_service.verify_phone_otp(
        session=session,
        otp_code=otp, 
        phone_number=phone_number, 
        invite_code=invite_code
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=f"{result['message']}")

    return result

@router.post('/user/email/otp/send')
async def send_email_otp(
    data: EmailSendOtpRequest
) -> EmailSendOtpResponse:
    try:
        result = await dummy_service.send_email_otp(
            email=data.email
        )

        return EmailSendOtpResponse(
            message=result["message"],
            success=True
        )
    except HTTPException as he:
        logger.error(f"HTTP error in send_email_otp: {he.detail}")
        raise he
    except Exception as e:
        logger.error(f"Unexpected error in send_email_otp: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while sending OTP"
        )

@router.post('/user/email/otp/verify')
async def verify_email_otp(
    data: EmailVerifyOtpRequest, 
    session: Annotated[AsyncSession, Depends(get_session)]
) -> EmailVerifyOtpResponse:
    try:
        result = await dummy_service.verify_email_otp(
            user_id = data.user_id,
            email=data.email,
            otp=data.otp, 
            session=session
            
        )
        return EmailVerifyOtpResponse(
            message=result["message"],
            success=result["success"]
        )
    except HTTPException as he:
        logger.error(f"HTTP error in verify_email_otp: {he.detail}")
        raise he
    except Exception as e:
        logger.error(f"Unexpected error in verify_email_otp: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while verifying OTP"
        )

@router.post("/user/choose-investor-type")
async def choose_investor_type(
    data: ChooseInvestorRequest, 
    session: Annotated[AsyncSession, Depends(get_session)]
) -> ChooseInvestorResponse :

    result = await dummy_service.choose_investor_type(
        user_id=data.user_id,
        investor_type=data.investor_type,
        session=session
    ) 
    
    return ChooseInvestorResponse(**result)

@router.post("/user/declaration")
async def declaration(
    data: DeclarationRequest, 
    session: Annotated[AsyncSession, Depends(get_session)]
) -> DeclarationResponse: 
    
    if not data.declaration_accepted:
        raise HTTPException(status_code=400, detail="Declaration must be accepted")

    result = await dummy_service.declaration_accepted(
        user_id=data.user_id, 
        declaration_accepted=data.declaration_accepted, 
        session=session
    )

    return DeclarationResponse(**result) 

@router.post("/user/professional-background") 
async def professional_back(
    data: ProfessionalBackgroundRequest, 
    session: Annotated[AsyncSession, Depends(get_session)]
) -> ProfessionalBackgroundResponse: 
    
    result = await dummy_service.set_professional_background(
        user_id = data.user_id,
        occupation = data.occupation,
        income_source = data.income_source,
        annual_income = data.annual_income,
        capital_commitment = data.capital_commitment,
        session=session
    )

    return ProfessionalBackgroundResponse(**result)

@router.post("/user/sign-agreement")
async def sign_agreement(
    data: AgreementRequest, 
    session: Annotated[AsyncSession, Depends(get_session)]
) -> Dict[str, Any]: 
    try:
        if not data.agreement_signed:
            raise HTTPException(status_code=400, detail="Agreement must be signed")

        # Create document from template
        document_metadata = await zoho_service.create_document_from_template(
            user_id=data.user_id,
            session=session
        )

        # Apply e-stamp to the document
        estamp_result = await zoho_service.apply_estamp(
            user_id=data.user_id,
            session=session
        )

        # # Send document for signing
        # send_result = await zoho_service.send_document_for_signing(
        #     user_id=str(data.user_id),
        #     session=session
        # )

        result = {
            "success": True,
            "message": "Document created, e-stamped, and sent for signing",
            "user_id": str(data.user_id),
            "request_id": document_metadata["request_id"],
            "document_id": document_metadata["document_id"],
            "document_result": document_metadata,
            "estamp_result": estamp_result,
        }

        logger.info(f"Agreement signing process initiated for user_id: {data.user_id}")
        return result

    except HTTPException as he:
        logger.error(f"HTTP error in sign_agreement: {he.detail}")
        raise he
    except Exception as e:
        logger.error(f"Unexpected error in sign_agreement: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process agreement signing: {str(e)}"
        )

@router.post("/user/upload-photo")
async def upload_photo( 
    session: Annotated[AsyncSession, Depends(get_session)], 
    data: PhotoUploadRequest = Depends(), image: UploadFile = File(...)
) -> PhotoUploadResponse:
    try:
        result = await dummy_service.upload_photograph(
            user_id=data.user_id,
            file=image,
            session=session
        )
        return PhotoUploadResponse(**result)
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to upload photo: {str(e)}")

# Use with caution for dev Access Only

@router.delete("/user/delete")
async def delete_user_record(
    phone_number: str,
    invitation_code: str, 
    session: Annotated[AsyncSession, Depends(get_session)]
) -> Dict[str, Any]: 
    try:
        result = await dummy_service.delete_user_record(
            phone_number=phone_number,
            invitation_code=invitation_code,
            session=session
        )
        return result
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to delete user record: {str(e)}")
    
@router.delete("/user/delete-all")
async def delete_all_users(
    session: Annotated[AsyncSession, Depends(get_session)]
) -> Dict[str, Any]:
    try:
        result = await dummy_service.delete_all_users(
            session=session
        )
        return result
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to delete all users: {str(e)}")