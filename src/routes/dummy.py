from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from starlette import status
from pydantic import EmailStr
from src.logging.logging_setup import get_logger
from src.db.session import get_session 
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated, Dict, Any
from src.schemas.kyc import (EmailVerifyOtpRequest, EmailVerifyOtpResponse, AgreementRequest, AgreementResponse, 
                            DeclarationRequest, DeclarationResponse, ChooseInvestorRequest, ChooseInvestorResponse, 
                            PhoneNumSendOtpRequest, EmailSendOtpRequest, EmailSendOtpResponse, PhoneNumSendOtpResponse, 
                            PhoneNumVerifyOtpRequest, PhoneNumVerifyOtpResponse, UserDetailsRequest, UserDetailsResponse, 
                            ProfessionalBackgroundRequest, ProfessionalBackgroundResponse, PhotoUploadRequest, PhotoUploadResponse
                            , UserOnboardingStartResponse, UserOnboardingStartRequest)
from src.services.dummy import DummyService
from src.services.email import EmailService

router = APIRouter() 

# service initialization 
dummy_service = DummyService()
email_service = EmailService()

logger = get_logger(__name__)

@router.post("/investor/signin/email/send-otp")
async def signin_investor_send_email_otp(
    session: Annotated[AsyncSession, Depends(get_session)], 
    email: EmailStr, 
) -> Dict[str, Any]:

    result = await dummy_service.investor_signin_email(
        session=session,
        email=email
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail="Invalid invitation code")

    return result

@router.post("/investor/signin/verify-otp")
async def signup_investor_verify_email_otp(
    session: Annotated[AsyncSession, Depends(get_session)], 
    email: EmailStr, 
    otp: str
) -> Dict[str, Any]:

    result = await dummy_service.investor_signin_email_verify(
        session=session,
        email=email,
        otp_code=otp
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail="Invalid invitation code")

    return result

@router.post("/user/invitation/validate")
async def validate_invitation(
    data: UserOnboardingStartRequest, 
    session: Annotated[AsyncSession, Depends(get_session)]
) -> UserOnboardingStartResponse:
    
    result: dict = await dummy_service.verify_invitation_code(
        invitation_code = data.invitation_code,
        session=session
    ) 
    if not result["success"]:
        raise HTTPException(status_code=400, detail="Invalid invitation code")

    return UserOnboardingStartResponse(user_id=result["user_id"], message="new user added")

@router.post('/user/phone/otp/send')
async def send_phone_otp(
    data: PhoneNumSendOtpRequest
) -> PhoneNumSendOtpResponse :
    
    result = await dummy_service.send_phone_otp(
        phone_number=data.phone_number, 
        session=Annotated[AsyncSession, Depends(get_session)]
    )
    return PhoneNumSendOtpResponse(**result) 
    
@router.post('/user/phone/otp/verify')
async def verify_phone_otp(
    data: PhoneNumVerifyOtpRequest, 
    session: Annotated[AsyncSession, Depends(get_session)]
) -> PhoneNumVerifyOtpResponse :

    result = await dummy_service.verify_phone_otp(
        otp_code= data.otp, 
        phone_number=data.phone_number, 
        user_id=data.user_id,
        session=session
    )

    return PhoneNumVerifyOtpResponse(**result)

@router.post("/user/details")
async def store_user_details(
    data: UserDetailsRequest, 
    session: Annotated[AsyncSession, Depends(get_session)]
) -> UserDetailsResponse:

    result = await dummy_service.set_user_details(
        user_id = data.user_id,
        first_name= data.first_name,
        last_name=data.last_name,
        session=session
    )

    return UserDetailsResponse(**result) 

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
) -> AgreementResponse: 

    result = await dummy_service.contribution_agreement(
        user_id=data.user_id,
        agreement_signed=data.agreement_signed,
        session=session
    )

    return AgreementResponse(**result)

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
