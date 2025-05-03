from pydantic import BaseModel, EmailStr
from typing import Optional, Dict
from uuid import UUID
from fastapi import UploadFile

class AadhaarRequest(BaseModel):
    unique_id: str
    aadhaar_number: str

class AadhaarResponse(BaseModel):
    transaction_id: str
    fwdp: str
    code_verifier: str
    message: str

class SubmitOTPRequest(BaseModel):
    otp: str
    transaction_id: str
    code_verifier: str
    fwdp: str

class SubmitOTPResponse(BaseModel):
    aadhaarNumber: str
    uniqueId: str
    referenceId: str
    maskedAadhaarNumber: str
    name: str
    gender: str
    dob: str
    careOf: Optional[str] = None
    passCode: str
    link: str
    address: Dict[str, str]
    image: str
    isXmlValid: str

class ResendOTPRequest(BaseModel):
    unique_id: str
    aadhaar_number: str
    transaction_id: str
    fwdp: str

class ResendOTPResponse(BaseModel):
    transaction_id: str
    fwdp: str
    code_verifier: str
    message: str

class PanDetailsRequest(BaseModel):
    unique_id: str
    pan_number: str

class PanDetailsResponse(BaseModel):
    pan: str
    status: str
    status_code: str
    name: Optional[str] = None
    dob: Optional[str] = None
    seeding_status: Optional[str] = None

class PhoneNumRequest(BaseModel):
    phone_number: str
    alias: Optional[str] = "UserVerification"
    channel: Optional[str] = "sms"

class PhoneNumResponse(BaseModel):
    message: str
    verification_uuid: str


class OTPVerificationRequest(BaseModel):
    session_uuid: str
    otp_code: str

class OTPVerificationResponse(BaseModel):
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

class UserDetailsResponse(BaseModel): 
    message: str
    user_id: UUID
    first_name: str
    last_name: str  

class EmailDetailsRequest(BaseModel):
    email: EmailStr
    pass 

class EmailDetailsResponse(BaseModel):
    pass 

class InvestorTypeRequest(BaseModel):
    pass 

class InvestorTypeResponse(BaseModel):
    pass 

class ProfessionalBackgroundRequest(BaseModel): 
    occupation: str
    income_source: str
    annual_income: str
    capital_commitment: float
 

class ProfessionalBackgroundResponse(BaseModel): 
    user_id: UUID
    message: str
    pass 

class PhotoUploadRequest(BaseModel):
    image: UploadFile
    expiration: int | None = 3600 


class PhotoUploadResponse(BaseModel):
    message: str
    user_id: UUID
 


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