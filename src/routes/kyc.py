from fastapi import APIRouter 
from fastapi.responses import JSONResponse
from starlette import status
from src.schemas.kyc import (   AadhaarRequest, AadhaarResponse,
                                SubmitOTPRequest,
                                ResendOTPRequest,
                                PanDetailsRequest
                            ) 

from src.schemas.kyc_validation import (    ValidateAadhaarRequest,
                                            ValidatePanRequest,
                                            PanAadhaarLinkRequest
                                        ) 
from src.services.aadhaar import AadhaarService
from src.services.pan import PANService
from src.services.phone import PhoneService
from src.services.kyc_validation import ValidationService
from src.services.user import UserService

# SubmitOTPResponse, PanDetailsResponse, ValidatePanResponse, PanAadhaarLinkResponse, ValidateAadhaarResponse, ResendOTPResponse   import after
aadhaar_service = AadhaarService() #initiate the service to use later in code. 
pan_service = PANService()  # initiate PAN service
phone_service = PhoneService() # initiate Phone service
validation_service = ValidationService() # intiate validation service 
user_service = UserService() # intiate user service 

router = APIRouter() 

@router.post('/aadhaar/otp/send')
async def verify_aadhaar(aadhaar_details: AadhaarRequest) -> AadhaarResponse:
    response_data = await aadhaar_service.initiate_kyc(
        unique_id=aadhaar_details.unique_id,
        aadhaar_number=aadhaar_details.aadhaar_number
    )

    content = AadhaarResponse(
        transaction_id=response_data["transaction_id"],
        fwdp=response_data["fwdp"],
        code_verifier=response_data["code_verifier"],
        message="OTP sent to Aadhaar registered mobile number"
    )

    return JSONResponse(status_code=status.HTTP_200_OK, content = content)

@router.post('/aadhaar/otp/verify', tags = ["aadhaar"])
async def submit_aadhaar_otp(otp_details: SubmitOTPRequest) -> dict:
    user_data = await aadhaar_service.submit_aadhaar_otp(
        otp=otp_details.otp,
        transaction_id=otp_details.transaction_id,
        code_verifier=otp_details.code_verifier,
        fwdp=otp_details.fwdp
    )

    content =  dict(**user_data) 
    return JSONResponse(status_code=status.HTTP_200_OK, content = content)

@router.post('/aadhaar/otp/resend', tags = ["aadhaar"])
async def resend_aadhaar_otp(otp_details: ResendOTPRequest) -> dict:
    response_data = await aadhaar_service.resend_aadhaar_otp(
        unique_id=otp_details.unique_id,
        aadhaar_number=otp_details.aadhaar_number,
        transaction_id=otp_details.transaction_id,
        fwdp=otp_details.fwdp
    )

    content = dict(**response_data)
    return JSONResponse(status_code=status.HTTP_200_OK, content = content)

@router.post("/aadhaar/validate", tags = ["aadhaar"])
async def validate_aadhaar(validation_details: ValidateAadhaarRequest) -> dict: # should change later to ValidateAadhaarResponse
    response_data = await validation_service.validate_aadhaar(
        client_ref_num=validation_details.client_ref_num,
        aadhaar_number=validation_details.aadhaar_number
    )

    content = dict(**response_data)
    return JSONResponse(status_code=status.HTTP_200_OK, content = content)

@router.post('/pan/verify', tags= ["pan"])
async def verify_pan(pan_details: PanDetailsRequest) -> dict:
    pan_data = await pan_service.verify_pan(
        unique_id=pan_details.unique_id,
        pan_number=pan_details.pan_number
    )

    content = dict(**pan_data)
    return JSONResponse(status_code=status.HTTP_200_OK, content=content)

@router.post("/pan/validate", tags= ["pan"])
async def validate_pan(validation_details: ValidatePanRequest) -> dict:
    response_data = await validation_service.validate_pan(
        client_ref_num=validation_details.client_ref_num,
        aadhaar_number=validation_details.pan_number,
        full_name=validation_details.full_name
    )

    content = dict(**response_data)
    return JSONResponse(status_code=status.HTTP_200_OK, content=content)

@router.post("/pan/aadhaar/link", tags= ["pan", "aadhaar"])
async def validate_pan_aadhaar_linked(validation_details: PanAadhaarLinkRequest) -> dict:
    response_data = await validation_service.validate_pan_aadhaar_link(
        client_ref_num = validation_details.client_ref_num,
        pan_number = validation_details.pan_number,
        aadhaar_number=validation_details.aadhaar_number
    )

    content = dict(**response_data) 
    return JSONResponse(status_code=status.HTTP_200_OK, content=content)












