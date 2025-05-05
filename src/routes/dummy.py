from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from starlette import status
from pydantic import BaseModel 
from uuid import UUID 
from src.db.session import get_session 
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from src.schemas.kyc import EmailVerifyOtpRequest, EmailVerifyOtpResponse, AgreementRequest, AgreementResponse, DeclarationRequest, DeclarationResponse, ChooseInvestorRequest, ChooseInvestorResponse, PhoneNumSendOtpRequest, EmailSendOtpRequest, EmailSendOtpResponse, PhoneNumSendOtpResponse, PhoneNumVerifyOtpRequest, PhoneNumVerifyOtpResponse, UserDetailsRequest, UserDetailsResponse, ProfessionalBackgroundRequest, ProfessionalBackgroundResponse, PhotoUploadRequest, PhotoUploadResponse
from src.services.dummy import DummyService

router = APIRouter() 

# service initialization 
dummy_service = DummyService()

# schemas : will move to schemas folder 
class UserOnboardingStartRequest(BaseModel):
    invitation_code: str
    
class UserOnboardingStartResponse(BaseModel):
    user_id: UUID
    message: str

@router.post("/invitation/validate")
async def validate_invitation(data: UserOnboardingStartRequest, session: Annotated[AsyncSession, Depends(get_session)]) -> UserOnboardingStartResponse:
    
    result: dict = await dummy_service.verify_invitation_code(
        invitation_code = data.invitation_code,
        session=session
    ) 
    if not result["success"]:
        raise HTTPException(status_code=400, detail="Invalid invitation code")

    return UserOnboardingStartResponse(user_id=result["user_id"], message="new user added")

@router.patch('/phone/otp/send')
async def send_phone_otp(onboarding_details: PhoneNumSendOtpRequest) -> PhoneNumSendOtpResponse :
    
    result = await dummy_service.send_phone_otp(
        phone_number=onboarding_details.phone_number
    )
    return PhoneNumSendOtpResponse(**result) 
    
@router.patch('/phone/otp/verify')
async def verify_phone_otp(data: PhoneNumVerifyOtpRequest) -> PhoneNumVerifyOtpResponse :

    result = await dummy_service.verify_phone_otp(
        otp_code= data.otp
    )

    content = dict(**result) 
    return JSONResponse(status_code= status.HTTP_200_OK, content=content) 

@router.patch("/user/details")
async def store_user_details(user_details: UserDetailsRequest, session: Annotated[AsyncSession, Depends(get_session)]) -> UserDetailsResponse:

    result = await dummy_service.set_user_details(
        user_id = user_details.user_id,
        first_name= user_details.first_name,
        last_name=user_details.last_name,
        session=session
    )

    return UserDetailsResponse(**result) 

@router.patch('/email/otp/send')
async def send_email_otp(onboarding_details: EmailSendOtpRequest) -> EmailSendOtpResponse :
    
    result = await dummy_service.send_email_otp(
        email=onboarding_details.email
    )
    return EmailSendOtpResponse(**result)  

@router.patch('/email/otp/verify')
async def verify_email_otp(data: EmailVerifyOtpRequest) -> EmailVerifyOtpResponse :

    result = await dummy_service.verify_email_otp(
        otp= data.otp
    )
    return EmailVerifyOtpResponse(**result)

@router.patch("/user/choose-investor-type")
async def choose_investor_type(data: ChooseInvestorRequest, session: Annotated[AsyncSession, Depends(get_session)]) -> ChooseInvestorResponse :

    result = await dummy_service.choose_investor_type(
        user_id=data.user_id,
        investor_type=data.investor_type,
        session=session
    ) 
    
    return ChooseInvestorResponse(**result)

@router.patch("/user/declaration")
async def declaration(data: DeclarationRequest, session: Annotated[AsyncSession, Depends(get_session)]) -> DeclarationResponse: 

    result = await dummy_service.declaration_accepted(
        user_id=data.user_id, 
        declaration_accepted=data.declaration_accepted, 
        session=session
    )

    return DeclarationResponse(**result) 

@router.patch("/user/professional-background") 
async def professional_back(data: ProfessionalBackgroundRequest, session: Annotated[AsyncSession, Depends(get_session)]) -> ProfessionalBackgroundResponse: 
    
    result = await dummy_service.set_professional_background(
        user_id = data.user_id,
        occupation = data.income_source,
        income_source = data.income_source,
        annual_income = data.annual_income,
        capital_commitment = data.capital_commitment,
        session=session
    )

    return ProfessionalBackgroundResponse(**result)

@router.patch("/user/sign-agreement")
async def sign_agreement(data: AgreementRequest, session: Annotated[AsyncSession, Depends(get_session)]) -> AgreementResponse: 

    result = await dummy_service.contribution_agreement(
        user_id=data.user_id,
        agreement_signed=data.agreement_signed,
        session=session
    )

    return AgreementResponse(**result)

@router.patch("/user/upload-photo") 
async def upload_photo(data: PhotoUploadRequest, session: Annotated[AsyncSession, Depends(get_session)]) -> PhotoUploadResponse: 
    
    result = dummy_service.upload_photograph(
        user_id = data.user_id,
        file = data.image, 
        session=session
    ) 

    content = PhotoUploadResponse(**result) 
    return JSONResponse(status_code=status.HTTP_200_OK, content=content) 

