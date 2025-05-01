from models.deal import Deal 
from models.investment import Investment
from models.kyc import KYC 
from models.user import User 
from sqlmodel import SQLModel

class Base(SQLModel):
    pass

Base.metadata.tables = [Deal.__table__, Investment.__table__,User.__table__, KYC.__table__]