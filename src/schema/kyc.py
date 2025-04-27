from pydantic import BaseModel, EmailStr
from typing import Optional, Dict

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


class OnBoardingRequest(BaseModel):
    pass 

class OnBoardingResponse(BaseModel):
    pass 

class UserDetailsRequest(BaseModel):
    pass 

class UserDetailsResponse(BaseModel): 
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

class PanDetailsRequest(BaseModel):
    pass 

class PanDetailsResponse(BaseModel):
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