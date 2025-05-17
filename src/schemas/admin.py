from pydantic import BaseModel, EmailStr

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





