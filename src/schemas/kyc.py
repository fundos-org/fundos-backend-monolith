from pydantic import BaseModel, EmailStr
from typing import Optional, Dict
from uuid import UUID
from src.models.user import investorType

class UserOnboardingStartRequest(BaseModel):
    invitation_code: str
    phone_number: str
    
class UserOnboardingStartResponse(BaseModel):
    user_id: UUID
    message: str
    success: bool 
    
class AadhaarRequest(BaseModel):
    user_id: str
    aadhaar_number: str

class AadhaarResponse(BaseModel):
    transaction_id: str
    fwdp: str
    code_verifier: str
    message: str

class SubmitOTPRequest(BaseModel):
    user_id: str
    otp: str

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

class ResendOTPResponse(BaseModel):
    transaction_id: str
    fwdp: str
    code_verifier: str
    message: str

class PanDetailsRequest(BaseModel):
    user_id: str
    pan_number: str

class PanDetailsResponse(BaseModel):
    pan: str
    status: str
    status_code: str
    name: Optional[str] = None
    dob: Optional[str] = None
    seeding_status: Optional[str] = None

class PhoneNumSendOtpRequest(BaseModel):
    phone_number: str
    alias: Optional[str] = "UserVerification"
    channel: Optional[str] = "sms"

class PhoneNumSendOtpResponse(BaseModel):
    message: str
    otp: str
    onboarding_status: str
    success: bool


class PhoneNumVerifyOtpRequest(BaseModel):
    phone_number: str
    otp: str
    user_id: UUID

class PhoneNumVerifyOtpResponse(BaseModel):
    message: str
    user_id: str
    success: bool

class OTPVerificationRequest(BaseModel):
    session_uuid: str
    otp_code: str

class OTPVerificationResponse(BaseModel):
    message: str
    session_uuid: str
    api_id: str

class EmailSendOtpRequest(BaseModel):
    email: EmailStr

class EmailSendOtpResponse(BaseModel):
    message: str
    success: bool

class EmailVerifyOtpRequest(BaseModel):
    user_id: UUID
    email: EmailStr
    otp: str 

class EmailVerifyOtpResponse(BaseModel):
    message: str 
    success: bool

class UserDetailsRequest(BaseModel):
    user_id: UUID
    first_name: str
    last_name: str 

class UserDetailsResponse(BaseModel): 
    message: str
    user_id: UUID
    first_name: str
    last_name: str  

class ChooseInvestorRequest(BaseModel):
    investor_type: investorType
    user_id: UUID

class ChooseInvestorResponse(BaseModel):
    message: str
    user_id: UUID 

class DeclarationRequest(BaseModel):
    declaration_accepted: bool
    user_id: UUID

class DeclarationResponse(BaseModel): 
    message: str
    user_id: UUID

class ProfessionalBackgroundRequest(BaseModel): 
    occupation: str
    income_source: str
    annual_income: float
    capital_commitment: float
    user_id: UUID
 

class ProfessionalBackgroundResponse(BaseModel): 
    message: str 
    user_id: UUID
    

class PhotoUploadRequest(BaseModel):
    expiration: int | None = 3600 
    user_id: UUID


class PhotoUploadResponse(BaseModel):
    message: str
    user_id: UUID
    image_url: str

class AgreementRequest(BaseModel):
    agreement_signed: bool
    user_id: UUID 

class AgreementResponse(BaseModel):
    message: str
    user_id: UUID 

class ResendOTPRequest(BaseModel):
    user_id: str
    aadhaar_number: str

class PanBankLinkRequest(BaseModel):
    user_id: str
    pan_number: str
    bank_account_number: str
    ifsc_code: str

