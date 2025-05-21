from pydantic import BaseModel
from typing import List
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
    transactions: List[TransactionDetail]
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
    company_name: str
    status: str
    round_size: float
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