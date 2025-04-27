from fastapi import APIRouter 
from schemas.kyc import ( AadhaarRequest, AadhaarResponse,
                         SubmitOTPRequest, SubmitOTPResponse,
                         ResendOTPRequest, ResendOTPResponse,
                         PhoneNumRequest, PhoneNumResponse, 
                         OTPVerificationRequest,OTPVerificationResponse,
                         UserDetailsRequest, UserDetailsResponse, 
                         EmailDetailsRequest, EmailDetailsResponse, 
                         InvestorTypeRequest, InvestorTypeResponse,
                         PanDetailsRequest, PanDetailsResponse
                        )
from services.aadhaar_service import AadhaarService
from services.pan_service import PANService
from services.phone_service import PhoneService


aadhaar_service = AadhaarService() #initiate the service to use later in code. 
pan_service = PANService()  # initiate PAN service
phone_service = PhoneService() # initiate Phone service

router = APIRouter() 

@router.post('/verify-aadhaar')
async def verify_aadhaar(aadhaar_details: AadhaarRequest) -> AadhaarResponse:
    response_data = await aadhaar_service.initiate_kyc(
        unique_id=aadhaar_details.unique_id,
        aadhaar_number=aadhaar_details.aadhaar_number
    )

    return AadhaarResponse(
        transaction_id=response_data["transaction_id"],
        fwdp=response_data["fwdp"],
        code_verifier=response_data["code_verifier"],
        message="OTP sent to Aadhaar registered mobile number"
    )

@router.post('/submit-aadhaar-otp')
async def submit_aadhaar_otp(otp_details: SubmitOTPRequest) -> SubmitOTPResponse:
    user_data = await aadhaar_service.submit_aadhaar_otp(
        otp=otp_details.otp,
        transaction_id=otp_details.transaction_id,
        code_verifier=otp_details.code_verifier,
        fwdp=otp_details.fwdp
    )

    return SubmitOTPResponse(**user_data) 

@router.post('/resend-aadhaar-otp')
async def resend_aadhaar_otp(otp_details: ResendOTPRequest) -> ResendOTPResponse:
    response_data = await aadhaar_service.resend_aadhaar_otp(
        unique_id=otp_details.unique_id,
        aadhaar_number=otp_details.aadhaar_number,
        transaction_id=otp_details.transaction_id,
        fwdp=otp_details.fwdp
    )

    return ResendOTPResponse(**response_data)

@router.post('/verify-pan')
async def verify_pan(pan_details: PanDetailsRequest) -> PanDetailsResponse:
    pan_data = await pan_service.verify_pan(
        unique_id=pan_details.unique_id,
        pan_number=pan_details.pan_number
    )

    return PanDetailsResponse(**pan_data)

@router.post('/verify-phone-number', response_model=PhoneNumResponse)
async def verify_phone_number(onboarding_details: PhoneNumRequest):
    
    result = await phone_service.verify_phone_number(
        phone_number=onboarding_details.phone_number,
        alias=onboarding_details.alias,
        channel=onboarding_details.channel
    )
    return PhoneNumResponse(**result)

@router.post('/verify-otp', response_model=OTPVerificationResponse)
async def verify_otp(request: OTPVerificationRequest):
    phone_service = PhoneService()
    
    result = await phone_service.verify_otp(
        session_uuid=request.session_uuid,
        otp_code=request.otp_code
    )

    return OTPVerificationResponse(
        message=result.get("message", "OTP verified successfully."),
        session_uuid=request.session_uuid,
        api_id=result.get("api_id", "")
    )


@router.post('/submit-user-details')
async def submit_user_details(user_details: UserDetailsRequest) -> UserDetailsResponse: 
    pass 


@router.post('/verify-email-id')
async def verify_email(email_details: EmailDetailsRequest) -> EmailDetailsResponse: 
    pass 

@router.post('/choose-investor-type')
async def choose_investor_type(investor_type: InvestorTypeRequest) -> InvestorTypeResponse:
    pass 










