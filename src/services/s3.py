import boto3
from botocore.exceptions import ClientError
from botocore.response import StreamingBody
from fastapi import UploadFile, HTTPException, BackgroundTasks
from typing import Optional
from urllib.parse import urlparse
from uuid import UUID

from fastapi.responses import StreamingResponse
from src.logging.logging_setup import get_logger
import mimetypes
from datetime import datetime

logger = get_logger(__name__)

class S3Service:
    def __init__(self, bucket_name: str, region_name: str = "ap-south-1"):
        self.bucket_name = bucket_name
        self.s3_client = boto3.client("s3", region_name=region_name)

    async def upload_file(self, file: UploadFile, object_name: Optional[str] = None) -> str:
        """
        Uploads a file to S3.
        :param file: UploadFile object from FastAPI
        :param object_name: S3 object name. If not specified, file.filename is used.
        :return: The object name in S3
        """
        if object_name is None:
            object_name = file.filename

        try:
            await file.seek(0)  # Reset file pointer
            self.s3_client.upload_fileobj(
                file.file,
                self.bucket_name,
                object_name,
                ExtraArgs={'ContentType': file.content_type}
            )
        except ClientError as e:
            logger.error(f"S3 upload failed: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to upload to S3")
        return object_name

    async def background_upload_file(
        self, 
        file_content: bytes, 
        object_name: str, 
        content_type: str
    ) -> None:
        """Upload file content to S3 in the background."""
        try:
            self.s3_client.put_object(
                Body=file_content,
                Bucket=self.bucket_name,
                Key=object_name,
                ContentType=content_type
            )
            logger.info(f"Successfully uploaded {object_name} to S3")
        except ClientError as e:
            logger.error(f"Background S3 upload failed for {object_name}: {str(e)}")
            raise

    async def generate_presigned_url(self, object_name: str, expiration: int = 3600) -> str:
        """
        Generates a presigned URL to access the uploaded file.
        :param object_name: S3 object name
        :param expiration: Time in seconds for the presigned URL to remain valid
        :return: Presigned URL as string
        """
        try:
            response = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": object_name},
                ExpiresIn=expiration,
            )
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to generate presigned URL")
        return response

    async def upload_and_get_url(self, object_id: UUID, file: UploadFile, bucket_name: str, folder_prefix: str, expiration: int = 3600) -> str:
        """
        Uploads a file to S3 and returns a presigned URL.
        :param file: UploadFile object from FastAPI
        :param bucket_name: S3 bucket name
        :param folder_prefix: Folder prefix for the S3 object
        :param expiration: Time in seconds for the presigned URL to remain valid
        :return: Presigned URL as string
        """
        try:
            # Generate unique object name
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            file_extension = mimetypes.guess_extension(file.content_type) or '.jpg'
            object_name = f"{folder_prefix}{object_id}_{timestamp}{file_extension}"

            # Upload file to S3
            await file.seek(0)  # Reset file pointer
            self.s3_client.upload_fileobj(
                file.file,
                bucket_name,
                object_name,
                ExtraArgs={'ContentType': file.content_type}
            )

            # Generate presigned URL
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': object_name},
                ExpiresIn=expiration
            )

            return url
        except ClientError as e:
            logger.error(f"Failed to upload file {file.filename}: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to upload to S3")
        except Exception as e:
            logger.error(f"Unexpected error uploading file {file.filename}: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")
        
    async def upload_and_get_key(self, object_id: UUID, file: UploadFile, bucket_name: str, folder_prefix: str) -> str:
        """
        Uploads a file to S3 and returns the object key.
        :param object_id: Unique identifier for the object
        :param file: UploadFile object from FastAPI
        :param bucket_name: S3 bucket name
        :param folder_prefix: Folder prefix for the S3 object
        :return: Object key as string
        """
        try:
            # Generate unique object name
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            file_extension = mimetypes.guess_extension(file.content_type) or '.jpg'
            object_name = f"{folder_prefix}{object_id}_{timestamp}{file_extension}"

            # Upload file to S3
            await file.seek(0)  # Reset file pointer
            self.s3_client.upload_fileobj(
                file.file,
                bucket_name,
                object_name,
                ExtraArgs={'ContentType': file.content_type}
            )

            return object_name
        except ClientError as e:
            logger.error(f"Failed to upload file {file.filename}: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to upload to S3")
        except Exception as e:
            logger.error(f"Unexpected error uploading file {file.filename}: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")

    async def delete_file(self, file_uri: str) -> None:
        """
        Deletes a file from S3 given its URI.
        :param file_uri: The full URI of the file in S3.
        """
        parsed_url = urlparse(file_uri)
        object_key = parsed_url.path.lstrip('/')

        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=object_key)
        except ClientError as e:
            logger.error(f"Failed to delete S3 object {object_key}: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to delete from S3")
        
    async def stream_file(
        self,
        object_key: str,
        download_filename: Optional[str] = None,
        content_type: Optional[str] = "application/vnd.android.package-archive"
    ) -> StreamingResponse:
        """
        Streams an S3 file for download via FastAPI.
        :param object_key: S3 object key (e.g., 'assets/app-release.apk')
        :param download_filename: Filename to be used in Content-Disposition
        :param content_type: MIME type of the file
        :return: StreamingResponse with file contents
        """
        try:
            s3_object = self.s3_client.get_object(Bucket=self.bucket_name, Key=object_key)
            body: StreamingBody = s3_object['Body']
            headers = {
                "Content-Disposition": f'attachment; filename="{download_filename or object_key.split("/")[-1]}"'
            }

            return StreamingResponse(
                body,
                media_type=content_type,
                headers=headers
            )
        except ClientError as e:
            logger.error(f"Failed to stream S3 object {object_key}: {str(e)}")
            raise HTTPException(status_code=404, detail="File not found")