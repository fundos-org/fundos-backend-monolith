from services.s3 import S3Service
from fastapi import Depends 
from fastapi.exceptions import HTTPException
from sqlmodel import select
from db.session import get_session
from uuid import UUID
from models.user import User
from sqlalchemy.ext.asyncio import AsyncSession

BUCKET_NAME = "your-s3-bucket-name"

def get_s3_service() -> S3Service:
    return S3Service(bucket_name=BUCKET_NAME)


async def get_user(user_id: UUID, session: AsyncSession = Depends(get_session)) -> User:
    user: User = session.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise HTTPException(404, "User not found")
    return user
