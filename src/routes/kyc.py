from fastapi import APIRouter 
from src.schemas.kyc import ( AadhaarRequest, AadhaarResponse,
                         SubmitOTPRequest, SubmitOTPResponse,
                         ResendOTPRequest, ResendOTPResponse,
                         PhoneNumRequest, PhoneNumResponse, 
                         OTPVerificationRequest,OTPVerificationResponse,
                         UserDetailsRequest, UserDetailsResponse, 
                         EmailDetailsRequest, EmailDetailsResponse, 
                         InvestorTypeRequest, InvestorTypeResponse,
                         PanDetailsRequest, PanDetailsResponse
                        )
from src.schemas.kyc_validation import (ValidateAadhaarRequest, ValidateAadhaarResponse,
                                        ValidatePanRequest,ValidatePanResponse,
                                        PanAadhaarLinkRequest, PanAadhaarLinkResponse
                                        )
from services.aadhaar import AadhaarService
from services.pan import PANService
from services.phone import PhoneService
from services.kyc_validation import ValidationService


aadhaar_service = AadhaarService() #initiate the service to use later in code. 
pan_service = PANService()  # initiate PAN service
phone_service = PhoneService() # initiate Phone service
validation_service = ValidationService() # intiate validation service

router = APIRouter() 

@router.post('/aadhaar/verify')
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

@router.post('/aadhaar/submit-otp', tags = ["aadhaar"])
async def submit_aadhaar_otp(otp_details: SubmitOTPRequest) -> SubmitOTPResponse:
    user_data = await aadhaar_service.submit_aadhaar_otp(
        otp=otp_details.otp,
        transaction_id=otp_details.transaction_id,
        code_verifier=otp_details.code_verifier,
        fwdp=otp_details.fwdp
    )

    return SubmitOTPResponse(**user_data) 

@router.post('/aadhaar/resend-otp', tags = ["aadhaar"])
async def resend_aadhaar_otp(otp_details: ResendOTPRequest) -> ResendOTPResponse:
    response_data = await aadhaar_service.resend_aadhaar_otp(
        unique_id=otp_details.unique_id,
        aadhaar_number=otp_details.aadhaar_number,
        transaction_id=otp_details.transaction_id,
        fwdp=otp_details.fwdp
    )

    return ResendOTPResponse(**response_data)

@router.post("/aadhaar/validate", tags = ["aadhaar"])
async def validate_aadhaar(validation_details: ValidateAadhaarRequest) -> ValidateAadhaarResponse:
    response_data = await validation_service.validate_aadhaar(
        client_ref_num=validation_details.client_ref_num,
        aadhaar_number=validation_details.aadhaar_number
    )

    return ValidateAadhaarResponse(**response_data)

@router.post('/pan/verify', tags= ["pan"])
async def verify_pan(pan_details: PanDetailsRequest) -> PanDetailsResponse:
    pan_data = await pan_service.verify_pan(
        unique_id=pan_details.unique_id,
        pan_number=pan_details.pan_number
    )

    return PanDetailsResponse(**pan_data)

@router.post("/pan/validate", tags= ["pan"])
async def validate_pan(validation_details: ValidatePanRequest) -> ValidatePanResponse:
    response_data = await validation_service.validate_pan(
        client_ref_num=validation_details.client_ref_num,
        aadhaar_number=validation_details.pan_number,
        full_name=validation_details.full_name
    )

    return ValidateAadhaarResponse(**response_data)

@router.post("/pan/aadhaar/link", tags= ["pan", "aadhaar"])
async def validate_pan_aadhaar_linked(validation_details: PanAadhaarLinkRequest) -> PanAadhaarLinkResponse:
    response_data = await validation_service.validate_pan_aadhaar_link(
        client_ref_num = validation_details.client_ref_num,
        pan_number = validation_details.pan_number,
        aadhaar_number=validation_details.aadhaar_number
    )

    return PanAadhaarLinkResponse(**response_data) 

@router.post('/phone-num/verify', tags = ["phone-num"])
async def verify_phone_number(onboarding_details: PhoneNumRequest) -> PhoneNumResponse :
    
    result = await phone_service.verify_phone_number(
        phone_number=onboarding_details.phone_number,
        alias=onboarding_details.alias,
        channel=onboarding_details.channel
    )
    return PhoneNumResponse(**result)

@router.post('/phone-num/submit-otp', response_model=OTPVerificationResponse)
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


@router.post('/user/submit-details')
async def submit_user_details(user_details: UserDetailsRequest) -> UserDetailsResponse: 
    pass 


@router.post('/email/verify')
async def verify_email(email_details: EmailDetailsRequest) -> EmailDetailsResponse: 
    pass 

@router.post('/choose-investor-type')
async def choose_investor_type(investor_type: InvestorTypeRequest) -> InvestorTypeResponse:
    pass 










