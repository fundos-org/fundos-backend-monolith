from pydantic import BaseModel 

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