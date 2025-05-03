from fastapi import APIRouter, Depends
from models.user import User
from db.session import get_session
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from uuid import UUID
from fastapi.responses import JSONResponse
from starlette import status
from schemas.onboarding import (PhoneNumRequest, PhoneNumResponse, 
                                UserDetailsRequest, UserDetailsResponse, 
                                EmailDetailsRequest, EmailDetailsResponse,
                                VerifyPhoneOtpRequest, VerifyPhoneOtpResponse
                                )
from services.phone import PhoneService
from services.onboarding import OnboardingService
from services.email import EmailService 
from utils.dependencies import get_user

router = APIRouter(tags = ["onboarding"])

# initiate services
phone_service = PhoneService()

# dependencies for onboarding
session_dependency = Annotated[AsyncSession, Depends(get_session)] 
get_user_dependency = Annotated[User, Depends(get_user)]


# schemas : will move to schemas folder 
class UserOnboardingStartResponse(BaseModel):
    user_id: UUID
    message: str

@router.post("/invitation/validate")
async def validate_invitation(invitation_code: str, session: session_dependency ) -> UserOnboardingStartResponse:
    # Validate code...
    user = User(invitation_code=invitation_code)
    session.add(user)
    session.commit()
    session.refresh(user)
    content= {"user_id": user.id, "message": "Invitation validated, onboarding started"}
    return JSONResponse(status_code=status.HTTP_201_CREATED, content= content) 

@router.patch('/phone-num/verify', tags = ["phone-num"])
async def verify_phone_number(onboarding_details: PhoneNumRequest) -> PhoneNumResponse :
    
    result = await phone_service.verify_phone_number(
        phone_number=onboarding_details.phone_number,
        alias=onboarding_details.alias,
        channel=onboarding_details.channel
    )
    content = PhoneNumResponse(**result) 
    return JSONResponse(status_code=status.HTTP_200_OK, content= content) 

@router.patch("/phone-num/verify-otp")
async def verify_phone_otp(verify_otp_details: VerifyPhoneOtpRequest) -> VerifyPhoneOtpResponse:

    result = await phone_service.verify_otp(
        session_uuid = verify_otp_details.session_uuid,
        otp = verify_otp_details.otp_code
    ) 

    content = VerifyPhoneOtpResponse(**result)
    JSONResponse(status_code=status.HTTP_200_OK, content=content)
    pass 

@router.patch("/user/details", tags = ["user-details"])
async def store_user_details(user_details: UserDetailsRequest) -> UserDetailsResponse:

    result = await OnboardingService.set_user_details(
        user_id = user_details.user_id,
        first_name= user_details.first_name,
        last_name=user_details.last_name,
    )

    content = UserDetailsResponse(**result)
    return JSONResponse(status_code=status.HTTP_200_OK, content = content)
    pass 

@router.patch('/email/verify')
async def verify_email(email_details: EmailDetailsRequest) -> EmailDetailsResponse: 
    
    result = EmailService.send_email_otp(
        email_details.email
    )

    content = EmailDetailsResponse(**result)
    return JSONResponse(status_code=status.HTTP_200_OK, content = content)
    pass 


