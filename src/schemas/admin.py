from pydantic import BaseModel, EmailStr
from typing import List
from uuid import UUID 

class CreateProfileReq(BaseModel):
    name: str
    email: EmailStr
    contact: str
    about: str 

class CreateCredentialsReq(BaseModel):
    subadmin_id: str
    username: str
    password: str
    re_entered_password: str
    app_name: str
    invite_code: str
    
class CreateProfileRes(BaseModel):
    name: str
    username: str
    password: str 
    invite_code: str

class SubadminDetails(BaseModel): 
    subadmin_id: UUID
    name: str
    email: EmailStr
    invite_code: str
    total_users: int
    active_deals: int
    onboarding_date: str  

class GetSubadminRes(BaseModel):
    subadmins: List[SubadminDetails]


class AdminSignInReq(BaseModel):
    username: str
    password: str
    

