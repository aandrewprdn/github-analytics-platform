from pathlib import Path

from github_analytics_platform.minio_client import MinioClient

LOCAL_ROOT = Path("ingestions/github-analytics/bronze/github/repositories")
BASE_KEY = "ingestions/github-analytics/bronze/github/repositories"


def upload_parquet_files():
    client = MinioClient()
    client.ensure_bucket()

    for file in LOCAL_ROOT.rglob("*.parquet"):
        relative_path = file.relative_to(LOCAL_ROOT)
        object_key = f"{BASE_KEY}/{relative_path.as_posix()}"

        client.upload_file(file, object_key)
