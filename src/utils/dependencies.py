from starlette import status
from fastapi import Depends 
from fastapi.exceptions import HTTPException
from sqlmodel import select
from sqlalchemy.engine import Result
from src.db.session import get_session
from uuid import UUID
from typing import Optional
from src.models.user import User
from src.models import KYC
from src.services.s3 import S3Service
from sqlalchemy.ext.asyncio import AsyncSession

BUCKET_NAME = "your-s3-bucket-name"

def get_s3_service() -> S3Service:
    return S3Service(bucket_name=BUCKET_NAME)


async def get_user(user_id: UUID, session: AsyncSession = None) -> User:
    if session is None:
        session = await get_session()

    statement = select(User).where(User.id == user_id)
    result: Result = await session.execute(statement)
    user: Optional[User] = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

async def get_kyc_row(user_id: UUID, session: AsyncSession = Depends(get_session)) -> KYC: 
    statement = select(KYC).where(KYC.user_id == user_id) 
    result: Result = await session.exec(statement) 
    kyc_row: Optional[KYC] = result.scalar_one_or_none()

    if not kyc_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, details="Kyc record not found")
    return kyc_row
 
