from pydantic import BaseModel
from typing import List, Dict

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

class SubAdminDashboardTransactionsRes(BaseModel):
    subadmin_id: str
    subadmin_name : str
    transactions: List # row of a table with columns: transaction_id, investor, invested_in(startup), amount, transaction_date
    success: bool
    
class SubAdminDashboardOverviewGraphRes(BaseModel):
    subadmin_id: str
    subadmin_name : str
    graph : List[Dict[str, int]] # [{"day_num(int)" : {"amount(int)", "deal_count(int)"}}]
    success: bool

class SubAdminDashboardActivitiesRes(BaseModel):
    subadmin_id: str  
    subadmin_name : str  
    transactions: List[Dict[str, str]]
    success: bool

class SubAdminDealsStatisticsRes(BaseModel):
    subadmin_id: str
    subadmin_name : str
    live_deals: int
    closed_deals: int
    total_capital_raised: int
    deals_this_month: int
    success: bool

class SubAdminDealsOverviewRes(BaseModel):
    subadmin_id: str
    subadmin_name: str
    active_deals: List
    closed_deals: List
    success: bool


