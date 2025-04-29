from services.s3_services import S3Service
from sqlmodel.ext.asyncio.session import AsyncSession
from services.db_services import get_session

BUCKET_NAME = "your-s3-bucket-name"

async def get_db() -> AsyncSession: # type: ignore
    async with get_session() as session:
        yield session

def get_s3_service() -> S3Service:
    return S3Service(bucket_name=BUCKET_NAME)