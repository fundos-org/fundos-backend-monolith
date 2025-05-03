from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID


class PhoneNumRequest(BaseModel):
    phone_number: str
    alias: Optional[str] = "UserVerification"
    channel: Optional[str] = "sms"

class PhoneNumResponse(BaseModel):
    message: str
    verification_uuid: str

class VerifyPhoneOtpRequest(BaseModel):
    session_uuid: str
    otp_code: str

class VerifyPhoneOtpResponse(BaseModel):
    message: str
    session_uuid: str
    api_id: str

class OnBoardingRequest(BaseModel):
    pass 

class OnBoardingResponse(BaseModel):
    pass 

class UserDetailsRequest(BaseModel):
    user_id: UUID
    first_name: str
    last_name: str 
    pass 

class UserDetailsResponse(BaseModel): 
    user_id: UUID
    pass 

class EmailDetailsRequest(BaseModel):
    email: EmailStr

    pass 

class EmailDetailsResponse(BaseModel):
    pass 

class InvestorTypeRequest(BaseModel):
    pass 

class InvestorTypeResponse(BaseModel):
    pass 










class KYCCreate(BaseModel):
    aadhaar_number: str
    pan_number: str
    bank_account_number: str
    bank_ifsc: str

class KYCOut(BaseModel):
    id: int
    user_id: int
    status: str
    verification_details: Optional[str]

#  validation schemas

class ValidateAadhaarRequest(BaseModel):
    client_ref_num: str
    aadhaar_number: str
    pass 

class ValidateAadhaarResponse(BaseModel):
    pass


class ValidatePanRequest(BaseModel):
    client_ref_num: str
    pan_number: str
    full_name: str
    pass  

class ValidatePanResponse(BaseModel):
    pass 

class PanAadhaarLinkRequest(BaseModel):
    client_ref_num: str
    pan_number: str
    aadhaar_number: str  

class PanAadhaarLinkResponse(BaseModel):
    pass 