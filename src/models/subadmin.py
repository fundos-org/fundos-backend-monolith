from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime
from uuid import uuid4, UUID
from pydantic import EmailStr



class Subadmin(SQLModel, table = True):
    id: UUID = Field(primary_key=True, default_factory=uuid4) 
    name: Optional[str] = Field(default=None)
    email: Optional[EmailStr] = Field(default=None)
    contact: Optional[str] = Field(default=None)
    about: Optional[str] = Field(default=None)
    logo: str = Field(default=None)

    username: str = Field(unique=True)
    password: str = Field(default=None) 
    re_entered_password: str = Field(default=None)
    app_name: str = Field(default=None)
    invite_code: str = Field(unique=True, default=None, index=True)

    created_at: datetime = Field(default_factory=lambda: datetime.now().replace(tzinfo=None))
    updated_at: Optional[datetime] = Field(default=None, nullable=True) 

    deals: List["Deal"] = Relationship(back_populates="fund_manager")  # type: ignore # noqa: F821
    users: List["User"] = Relationship(back_populates="fund_manager_id")  # type: ignore # noqa: F821


