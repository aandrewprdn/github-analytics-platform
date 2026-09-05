from pathlib import Path

import boto3
from botocore.exceptions import ClientError
import os

import logging
logger = logging.getLogger(__name__)

class MinioClient:
    def __init__(self):
        self.bucket_name = os.getenv("MINIO_BUCKET_NAME")

        self.client = boto3.client(
            "s3",
            endpoint_url=os.getenv("MINIO_ENDPOINT_URL"),
            aws_access_key_id=os.getenv("MINIO_ROOT_USER"),
            aws_secret_access_key=os.getenv("MINIO_ROOT_PASSWORD")
        )
        self.base_key = os.getenv("MINIO_BASE_KEY")

    def ensure_bucket(self):
        try:
            self.client.head_bucket(Bucket=self.bucket_name)
        except ClientError:
            logger.info("Creating bucket %s", self.bucket_name)
            self.client.create_bucket(Bucket=self.bucket_name)

    def upload_file(self, local_path: Path, key: str):
        logger.info("Uploading %s -> s3://%s/%s", local_path, self.bucket_name, key)

        self.client.upload_file(
            Filename=str(local_path),
            Bucket=self.bucket_name,
            Key=key,
        )

