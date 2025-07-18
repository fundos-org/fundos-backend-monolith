from pydantic import BaseModel
from typing import List, Optional
from src.models.user import KycStatus, Role

class SubAdminSignInReq(BaseModel):
    username: str
    password: str

class SubAdminDashboardStatisticsRes(BaseModel):
    subadmin_id: str
    subadmin_name: str
    total_capital_committed: int
    listed_startups: int
    onboarded_investors: int
    deals_this_month: int
    success: bool

class TransactionDetail(BaseModel):
    transaction_id: str
    investor: str
    invested_in: str
    amount: float
    transaction_date: str

class OnboardingDetail(BaseModel):
    investor_id: str
    investor_name: str
    joined_date: str 

class InvestorKycDetail(BaseModel):
    investor_id: str
    investor_name: str
    kyc_completed_date: KycStatus

class SubAdminDashboardTransactionsRes(BaseModel):
    subadmin_id: str
    subadmin_name: str
    transactions: List[TransactionDetail]
    success: bool

class GraphData(BaseModel):
    day_num: int
    amount: int
    deal_count: int

class SubAdminDashboardOverviewGraphRes(BaseModel):
    subadmin_id: str
    subadmin_name: str
    graph: List[GraphData]
    success: bool

class SubAdminDashboardActivitiesRes(BaseModel):
    subadmin_id: str
    subadmin_name: str
    transaction_activities: List[TransactionDetail]
    onboarding_activities: List[OnboardingDetail]
    investor_kyc_activities: List[InvestorKycDetail]
    success: bool

class SubAdminDealsStatisticsRes(BaseModel):
    subadmin_id: str
    subadmin_name: str
    live_deals: int
    closed_deals: int
    total_capital_raised: int
    deals_this_month: int
    success: bool

class DealDetail(BaseModel):
    deal_id: str
    description: str
    title: str
    deal_status: str
    current_valuation: float
    round_size: float
    commitment: float
    business_model: str
    company_stage: str 
    logo_url: str
    created_at: str

class SubAdminDealsOverviewRes(BaseModel):
    subadmin_id: str
    subadmin_name: str
    active_deals: List[DealDetail]
    closed_deals: List[DealDetail]
    success: bool

class Member(BaseModel):
    user_id: str
    first_name: str
    last_name: str
    email: str
    capital_committed: float
    kyc_status: KycStatus

class Members(BaseModel):
    investors: List[Member]
    startups: List[Member]

class Statistics(BaseModel):
    onboarded: int
    kyc_pending: int
    started_investing: int

class MembersStatistics(BaseModel):
    investors_statistics: Statistics
    startups_statistics: Statistics

class SubAdminMembersStatisticsRes(BaseModel):
    subadmin_id: str
    subadmin_name: str
    invite_code: str
    members: Members
    statistics: MembersStatistics
    success: bool

class SubAdminAddMembersRes(BaseModel):
    user_id: str
    first_name: str
    last_name: str
    email: str
    role: Role
    success: bool

class InvestorListItem(BaseModel):
    investor_id: str
    name: str
    mail: str
    type: str
    deals_invested: int
    kyc_status: KycStatus
    mca_key: str
    joined_on: str
    profile_pic: str
    capital_commitment: float

class InvestorListMetadata(BaseModel):
    investor_onboarded: int
    kyc_pending: int
    started_investing: int

class InvestorListResponse(BaseModel):
    subadmin_id: str
    subadmin_name: str
    investors: List[InvestorListItem]
    pagination: dict
    success: bool

class InvestorMetadataResponse(BaseModel):
    subadmin_id: str
    subadmin_name: str
    metadata: InvestorListMetadata
    success: bool

class PaginationInfo(BaseModel):
    page: int
    per_page: int
    total_records: int
    total_pages: int
    has_next: bool
    has_prev: bool

class DeleteInvestorRequest(BaseModel):
    investor_id: str

class DeleteInvestorResponse(BaseModel):
    subadmin_id: str
    investor_id: str
    message: str
    success: bool

class UpdateInvestorRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    occupation: Optional[str] = None
    income_source: Optional[str] = None
    annual_income: Optional[float] = None
    capital_commitment: Optional[float] = None
    

class UpdateInvestorResponse(BaseModel):
    subadmin_id: str
    investor_id: str
    message: str
    success: bool

class PersonalDetails(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    pan_number: Optional[str] = None
    aadhaar_number: Optional[str] = None

class BankDetails(BaseModel):
    bank_account_number: Optional[str] = None
    bank_ifsc: Optional[str] = None
    account_holder_name: Optional[str] = None

class ProfessionalBackground(BaseModel):
    occupation: Optional[str] = None
    income_source: Optional[str] = None
    annual_income: Optional[float] = None
    capital_commitment: Optional[float] = None

class InvestorInfoResponse(BaseModel):
    investor_id: str
    personal_details: PersonalDetails
    bank_details: BankDetails
    professional_background: ProfessionalBackground
    success: bool

class DealInfo(BaseModel):
    company_name: str
    about_company: str
    industry: str
    company_stage: str
    logo_url: str
    status: str
    created_at: str
    deal_capital_commitment: Optional[float] = None
    equity: Optional[float] = None
    term_sheet: Optional[str] = None

class InvestorMetadata(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    investor_type: str
    role: str
    capital_commitment: Optional[float] = None
    profile_image_url: Optional[str] = None
    created_at: str
    total_deals: int

class InvestorInvestmentsResponse(BaseModel):
    investor_id: str
    deals: List[DealInfo]
    success: bool

class InvestorInvestmentsMetadataResponse(BaseModel):
    investor_id: str
    metadata: InvestorMetadata
    success: bool

class InvestorTransactionItem(BaseModel):
    transaction_type: str
    amount: float
    currency: str
    status: str
    created_at: str
    invitation_code: str

class InvestorTransactionsResponse(BaseModel):
    investor_id: str
    transactions: List[InvestorTransactionItem]
    success: bool

class InvestorDocumentsInfo(BaseModel):
    mca_key: Optional[str] = None
    share_certificate_key: Optional[str] = None
    term_sheet_key: Optional[str] = None

class InvestorDocumentsResponse(BaseModel):
    investor_id: str
    documents: InvestorDocumentsInfo
    success: bool

class MarkDealInactiveRequest(BaseModel):
    deal_id: str

class MarkDealInactiveResponse(BaseModel):
    subadmin_id: str
    deal_id: str
    message: str
    success: bool

class EditDealRequest(BaseModel):
    # Company Details
    logo_url: Optional[str] = None
    company_name: Optional[str] = None
    about_company: Optional[str] = None
    company_website: Optional[str] = None
    problem_statement: Optional[str] = None
    
    # Market Details
    industry: Optional[str] = None
    business_model: Optional[str] = None
    company_stage: Optional[str] = None
    
    # Deal Details
    current_valuation: Optional[float] = None
    round_size: Optional[float] = None
    syndicate_commitment: Optional[float] = None
    conversion_terms: Optional[str] = None
    instrument_type: Optional[str] = None
    pitch_deck_url: Optional[str] = None
    pitch_video_url: Optional[str] = None

class EditDealResponse(BaseModel):
    subadmin_id: str
    deal_id: str
    message: str
    success: bool

class DealDetailsInfo(BaseModel):
    # Company Details
    logo_url: Optional[str] = None
    company_name: Optional[str] = None
    about_company: Optional[str] = None
    company_website: Optional[str] = None
    problem_statement: Optional[str] = None
    
    # Market Details
    industry: Optional[str] = None
    business_model: Optional[str] = None
    company_stage: Optional[str] = None
    
    # Deal Details
    current_valuation: Optional[float] = None
    round_size: Optional[float] = None
    syndicate_commitment: Optional[float] = None
    conversion_terms: Optional[str] = None
    instrument_type: Optional[str] = None
    pitch_deck_url: Optional[str] = None
    pitch_video_url: Optional[str] = None

class DealDetailsResponse(BaseModel):
    subadmin_id: str
    deal_id: str
    deal_details: DealDetailsInfo
    success: bool

class DealAboutInfo(BaseModel):
    company_name: Optional[str] = None
    company_website: Optional[str] = None
    company_email: Optional[str] = None
    industry: Optional[str] = None
    business_model: Optional[str] = None

class DealAboutResponse(BaseModel):
    subadmin_id: str
    deal_id: str
    about_info: DealAboutInfo
    success: bool

class DealInvestorItem(BaseModel):
    investor_id: str
    first_name: str
    last_name: str
    investor_type: str
    commitments: float
    created_at: str
    status: str
    term_sheet_key: str
    deal_investor_status: int

class DealInvestorsResponse(BaseModel):
    deal_id: str
    investors: List[DealInvestorItem]
    pagination: dict
    success: bool

class DealTransactionItem(BaseModel):
    transaction_id: str
    invitation_code: str
    transaction_type: str
    amount: float
    created_at: str
    status: str

class DealTransactionsResponse(BaseModel):
    deal_id: str
    transactions: List[DealTransactionItem]
    pagination: dict
    success: bool

class DealDocumentsInfo(BaseModel):
    pitchdeck_final_key: Optional[str] = None
    video_pitch_key: Optional[str] = None

class DealDocumentsResponse(BaseModel):
    deal_id: str
    documents: DealDocumentsInfo
    success: bool

class WelcomeMailInfo(BaseModel):
    subject: str
    body: str

class WelcomeMailResponse(BaseModel):
    subadmin_id: str
    welcome_mail: WelcomeMailInfo
    success: bool

class WelcomeMailUpdateRequest(BaseModel):
    subject: str
    body: str

class WelcomeMailUpdateResponse(BaseModel):
    subadmin_id: str
    message: str
    success: bool

class OnboardingMailInfo(BaseModel):
    subject: str
    body: str

class OnboardingMailResponse(BaseModel):
    subadmin_id: str
    onboarding_mail: OnboardingMailInfo
    success: bool

class OnboardingMailUpdateRequest(BaseModel):
    subject: str
    body: str

class OnboardingMailUpdateResponse(BaseModel):
    subadmin_id: str
    message: str
    success: bool

class ConsentMailInfo(BaseModel):
    subject: str
    body: str

class ConsentMailResponse(BaseModel):
    subadmin_id: str
    consent_mail: ConsentMailInfo
    success: bool

class ConsentMailUpdateRequest(BaseModel):
    subject: str
    body: str

class ConsentMailUpdateResponse(BaseModel):
    subadmin_id: str
    message: str
    success: bool

# Combined email schemas
class EmailTemplateInfo(BaseModel):
    subject: str
    body: str

class CombinedEmailResponse(BaseModel):
    subadmin_id: str
    welcome_mail: EmailTemplateInfo
    onboarding_mail: EmailTemplateInfo
    consent_mail: EmailTemplateInfo
    success: bool

class EmailUpdateRequest(BaseModel):
    welcome_mail: Optional[EmailTemplateInfo] = None
    onboarding_mail: Optional[EmailTemplateInfo] = None
    consent_mail: Optional[EmailTemplateInfo] = None

class CombinedEmailUpdateResponse(BaseModel):
    subadmin_id: str
    message: str
    success: bool

# Subadmin listing schemas
class SubadminListItem(BaseModel):
    subadmin_id: str
    subadmin_name: str

class SubadminListResponse(BaseModel):
    subadmins: List[SubadminListItem]
    pagination: dict
    success: bool