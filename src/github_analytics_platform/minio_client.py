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
        # Prefix for bronze objects; the default keeps the existing key layout.
        self.base_key = os.getenv(
            "MINIO_BASE_KEY", "ingestions/github-analytics/bronze/github/repositories"
        ).strip("/")

    def ensure_bucket(self):
        try:
            self.client.head_bucket(Bucket=self.bucket_name)
            return True
        except ClientError:
            logger.info("Creating bucket %s", self.bucket_name)
            self.client.create_bucket(Bucket=self.bucket_name)
            return False

    def upload_file(self, local_path: Path, key: str):
        logger.info("Uploading %s -> s3://%s/%s", local_path, self.bucket_name, key)

        self.client.upload_file(
            Filename=str(local_path),
            Bucket=self.bucket_name,
            Key=key,
        )

    def put_bytes(self, key: str, data: bytes, content_type: str = "application/octet-stream"):
        """Write an in-memory object; overwrites an existing object with the same key."""
        logger.info("Writing %s bytes -> s3://%s/%s", len(data), self.bucket_name, key)
        self.client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=data,
            ContentType=content_type,
        )

    def read_bytes(self, key: str) -> bytes:
        """Read a whole object into memory (fine for small bronze Parquet pages)."""
        logger.info("Reading s3://%s/%s", self.bucket_name, key)
        response = self.client.get_object(Bucket=self.bucket_name, Key=key)
        return response["Body"].read()

    def download_file(self, key: str, local_path: str):
        logger.info("Downloading s3://%s/%s -> %s", self.bucket_name, key, local_path)

        self.client.download_file(
            Bucket=self.bucket_name,
            Key=key,
            Filename=local_path
        )

