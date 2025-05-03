import boto3
from botocore.exceptions import ClientError
from fastapi import UploadFile
from fastapi.exceptions import HTTPException
from typing import Optional
import logging
from urllib.parse import urlparse
from uuid import uuid4 
from src.logging.logging_setup import get_logger

logger = get_logger(__name__)

class S3Service:
    def __init__(self, bucket_name: str, region_name: str = "us-east-1"):
        self.bucket_name = bucket_name
        self.s3_client = boto3.client("s3", region_name=region_name)

    def upload_file(self, file: UploadFile, object_name: Optional[str] = None) -> str:
        """
        Uploads a file to S3.
        :param file: UploadFile object from FastAPI
        :param object_name: S3 object name. If not specified, file.filename is used.
        :return: The object name in S3
        """
        if object_name is None:
            object_name = file.filename

        try:
            self.s3_client.upload_fileobj(file.file, self.bucket_name, object_name)
        except ClientError as e:
            logging.error(e)
            raise e
        return object_name

    def generate_presigned_url(self, object_name: str, expiration: int = 3600) -> str:
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
            logging.error(e)
            raise e
        return response
    
    def upload_and_get_url(self, file: UploadFile, bucket_name: str, folder_prefix = str, expiration:int = 3600 ) -> str:
        try:
            # Generate a unique object name
            object_name = f"profiles/{uuid4()}_{file.filename}"
            
            # Upload file to S3
            self.s3_client.upload_fileobj(file.file, bucket_name, object_name)
            
            # Generate presigned URL for accessing the file
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': object_name},
                ExpiresIn=3600
            ) 

            return url 
        except ClientError as e:
            logger.error(f"{e} while upload file {file.filename}")
            raise HTTPException(status_code=500, detail=str(e))
         
    
    def delete_file(self, file_uri: str) -> None:
        """
        Deletes a file from S3 given its URI.
        :param file_uri: The full URI of the file in S3.
        """
        parsed_url = urlparse(file_uri)
        object_key = parsed_url.path.lstrip('/')

        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=object_key)
        except ClientError as e:
            logging.error(e)
            raise e
