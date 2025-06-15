from fastapi import APIRouter, Depends
from src.services.s3 import S3Service
from src.configs.configs import aws_config


router = APIRouter()
bucket_name = aws_config.aws_bucket
s3_service = S3Service(bucket_name=bucket_name)

@router.get("/app", summary="Download the Android App APK")
async def download_apk():
    return await s3_service.stream_file(
        object_key="assets/app-release.apk",
        download_filename="fundos-app.apk"
    )

