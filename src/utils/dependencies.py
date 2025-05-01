from src.services.s3_services import S3Service

BUCKET_NAME = "your-s3-bucket-name"

def get_s3_service() -> S3Service:
    return S3Service(bucket_name=BUCKET_NAME)