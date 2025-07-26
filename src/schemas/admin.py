from pydantic import BaseModel, EmailStr
from typing import List, Optional
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
    pagination: dict


class AdminSignInReq(BaseModel):
    username: str
    password: str
    

class SubadminListItem(BaseModel):
    subadmin_id: UUID
    subadmin_name: str
    email: EmailStr
    invitation_code: str
    onboarding_date: str
    total_users: int
    active_deals: int

class SubadminListPaginatedResponse(BaseModel):
    subadmins: list[SubadminListItem]
    pagination: dict
    success: bool

class SubadminDetailsResponse(BaseModel):
    subadmin_id: UUID
    logo: Optional[str] = None
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    contact: Optional[str] = None
    about: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    reenter_password: Optional[str] = None
    app_name: Optional[str] = None
    invite_code: Optional[str] = None
    app_theme: Optional[str] = None
    success: bool

class SubadminDetailsUpdateRequest(BaseModel):
    logo: Optional[str] = None
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    contact: Optional[str] = None
    about: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    reenter_password: Optional[str] = None
    app_name: Optional[str] = None
    invite_code: Optional[str] = None
    app_theme: Optional[str] = None

class SubadminDetailsUpdateResponse(BaseModel):
    subadmin_id: UUID
    message: str
    success: bool

class AdminDashboardMetadataResponse(BaseModel):
    total_admin_onboarded: int
    total_users: int
    active_deals: int
    new_user_this_month: int
    success: bool

class AdminOverviewItem(BaseModel):
    admin_id: str
    admin_name: str
    email: str
    invitation_code: str
    total_users: int
    active_deals: int
    onboarding_date: str

class PaginationInfo(BaseModel):
    page: int
    per_page: int
    total_records: int
    total_pages: int
    has_next: bool
    has_prev: bool

class AdminOverviewPaginatedResponse(BaseModel):
    admins: List[AdminOverviewItem]
    pagination: PaginationInfo
    success: bool
