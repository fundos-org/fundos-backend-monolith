from fastapi import APIRouter, Depends
from src.models.user import User, investorType
from src.db.session import get_session
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from uuid import UUID
from fastapi.responses import JSONResponse
from starlette import status
from src.schemas.onboarding import (PhoneNumRequest, PhoneNumResponse, 
                                UserDetailsRequest, UserDetailsResponse, 
                                EmailDetailsRequest, EmailDetailsResponse,
                                VerifyPhoneOtpRequest, VerifyPhoneOtpResponse, 
                                ProfessionalBackgroundRequest, ProfessionalBackgroundResponse,
                                PhotoUploadRequest, PhotoUploadResponse
                                )

from src.services.phone import PhoneService
from src.services.onboarding import OnboardingService
from src.services.email import EmailService 
from src.services.user import UserService
from src.utils.dependencies import get_user


router = APIRouter()

# initiate services
phone_service = PhoneService()
email_service = EmailService()
user_service = UserService()

# dependencies for onboarding
session_dependency = Annotated[AsyncSession, Depends(get_session)] 
get_user_dependency = Annotated[User, Depends(get_user)]


# schemas : will move to schemas folder 
class UserOnboardingStartResponse(BaseModel):
    user_id: UUID
    message: str

@router.post("/invitation/validate", tags = ["user"])
async def validate_invitation(invitation_code: str, session: session_dependency ) -> UserOnboardingStartResponse:
    # Validate code...
    user = User(invitation_code=invitation_code)
    session.add(user)
    session.commit()
    session.refresh(user)
    content= {"user_id": user.id, "message": "Invitation validated, onboarding started"}
    return JSONResponse(status_code=status.HTTP_201_CREATED, content= content) 

@router.patch('/phone/otp/send', tags = ["phone"])
async def verify_phone_number(onboarding_details: PhoneNumRequest) -> PhoneNumResponse :
    
    result = await phone_service.verify_phone_number(
        phone_number=onboarding_details.phone_number,
        alias=onboarding_details.alias,
        channel=onboarding_details.channel
    )
    content = PhoneNumResponse(**result) 
    return JSONResponse(status_code=status.HTTP_200_OK, content= content) 

@router.patch("/phone/otp/verify", tags= ["phone"])
async def verify_phone_otp(verify_otp_details: VerifyPhoneOtpRequest) -> VerifyPhoneOtpResponse:

    result = await phone_service.verify_otp(
        session_uuid = verify_otp_details.session_uuid,
        otp = verify_otp_details.otp_code
    ) 

    content = VerifyPhoneOtpResponse(**result)
    JSONResponse(status_code=status.HTTP_200_OK, content=content)
    pass 

@router.patch("/user/details", tags = ["user"])
async def store_user_details(user_details: UserDetailsRequest) -> UserDetailsResponse:

    result = await OnboardingService.set_user_details(
        user_id = user_details.user_id,
        first_name= user_details.first_name,
        last_name=user_details.last_name,
    )

    content = UserDetailsResponse(**result)
    return JSONResponse(status_code=status.HTTP_200_OK, content = content)
    pass 

@router.patch('/email/otp/send')
async def verify_email(email_details: EmailDetailsRequest) -> EmailDetailsResponse: 
    
    result = EmailService.send_email_otp(
        email_details.email
    )

    content = EmailDetailsResponse(**result)
    return JSONResponse(status_code=status.HTTP_200_OK, content = content)
    
@router.patch('/email/otp/verify', tags = ["email"])
async def verify_email_otp(data: dict) -> dict :

    result = await email_service.verify_email_otp(
        otp_code= data.otp
    )

    content = dict(**result) 
    return JSONResponse(status_code= status.HTTP_200_OK, content=content) 

@router.patch("/user/choose-investor-type",tags = ["user"])
async def choose_investor_type(user_id: str, data: investorType) -> dict :

    result = await user_service.choose_investor_type(
        user_id=user_id,
        investor_type=data
    ) 
    
    content = dict(**result) 
    return JSONResponse(status_code= status.HTTP_200_OK, content=content) 

@router.patch("/user/declaration", tags = ["user"])
async def declaration(user_id: str, declaration_accepted: bool) -> dict: 

    result = user_service.declaration_accepted(
        user_id=user_id, 
        declaration_accepted=declaration_accepted
    )

    content = result 
    return JSONResponse(status_code=status.HTTP_200_OK, content=content)

@router.patch("/user/professional-background",tags = ["user"]) 
async def professional_back(user_id: str, data: ProfessionalBackgroundRequest) -> ProfessionalBackgroundResponse: 
    
    result = user_service.set_professional_background(
        user_id = user_id,
        occupation = data.income_source,
        income_source = data.income_source,
        annual_income = data.annual_income,
        capital_commitment = data.capital_commitment
    )

    content = ProfessionalBackgroundResponse(**result)
    return JSONResponse(status_code=status.HTTP_200_OK, content=content)

@router.patch("/user/sign-agreement", tags = ["user"])
async def sign_agreement(user_id : UUID, agreement_signed: bool) -> dict: 

    result = user_service.contribution_agreement(
        user_id=user_id,
        agreement_signed=agreement_signed
    )

    content = result 
    return JSONResponse(status_code=status.HTTP_200_OK, content= content) 

@router.patch("/user/photo-upload", tags = ["user"]) 
async def upload_photo(user_id : UUID, data: PhotoUploadRequest) -> PhotoUploadResponse: 
    
    result = user_service.upload_photograph(
        user_id = user_id,
        file = data.image_file
    ) 

    content = PhotoUploadResponse(**result) 
    return JSONResponse(status_code=status.HTTP_200_OK, content=content) 

