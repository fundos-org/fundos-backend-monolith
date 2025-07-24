from fastapi import APIRouter
from src.services.s3 import S3Service
from src.configs.configs import aws_config, app_config


router = APIRouter()
bucket_name = aws_config.aws_bucket
s3_service = S3Service(bucket_name=bucket_name)

@router.get("/app", summary="Download the Android App APK")
async def download_apk():
    return await s3_service.stream_file(
        object_key=app_config.apk_key,
        download_filename="fundos-app.apk"
    )

