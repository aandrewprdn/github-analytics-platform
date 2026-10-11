import os
import json
from datetime import datetime
from pathlib import Path
import polars as pl
import logging

from airflow.sdk import dag, task
from sqlalchemy import BigInteger, Column, MetaData, Table, Text, create_engine

from github_analytics_platform.copy_ingestions_postgre import transform_before_db
from github_analytics_platform.github_client import GithubClient
from github_analytics_platform.minio_client import MinioClient

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


TEST_QUERY = "dataengineer language:python"
PAGES_TO_FETCH = 10
POSTGRES_URL = f"postgresql+psycopg://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:5432/{os.getenv('POSTGRES_DB')}"

@dag("github_extract_pipeline")
def github_extract_pipeline():
    local_ingestions_path = Path(os.environ["LOCAL_INGESTIONS_PATH"])
    

    @task
    def extract_and_save_bronze(q: str, per_page: int = 10, page:int = 1) -> dict:
        """
        Collect GitHub repository data and save it to a Parquet file.

        Args:
            q (str): The search query for GitHub repositories.
            per_page (int): Number of results per page (default is 10).
            pages_to_fetch (int): Number of pages to fetch (default is 1).
        
        Returns:
            metadata of processed and saved page
            {
                "page": 1,
                "ingestion_date": "2026-09-05",
                "file_path": "ingestions/.../page_001.parquet",
                "records": 100
            }
        """
        with GithubClient() as client:
            page_data = client.search_repos(q=q, per_page=per_page, page=page)

            df = pl.DataFrame(page_data["items"]).with_columns(
                pl.lit(page_data["_metadata"]).alias("_metadata"),
            )

            ingestion_date = datetime.fromisoformat(page_data["_metadata"]["ingested_at"]).date().isoformat()
            page_num = page_data["_metadata"].get("page", 1)

            output_file_path = f"{local_ingestions_path}/ingestion_date={ingestion_date}/page_{page_num}.parquet"
            logger.info(f"Saving JSON data to Parquet file: {output_file_path}")
            df = pl.DataFrame(df.to_dict())
            df.write_parquet(output_file_path, mkdir=True)

            return {
                "page": page,
                "ingestion_date": ingestion_date,
                "file_path": output_file_path,
                "per_page": per_page
            }

    @task
    def ensure_minio_bucket():
        client = MinioClient()
        client.ensure_bucket()

    @task
    def upload_bronze_to_minio(file_info: dict):
        client = MinioClient()

        file = Path(file_info["file_path"])

        client.upload_file(file, file_info["file_path"])

    @task
    def ensure_raw_table():
        metadata = MetaData()

        Table(
            os.environ["POSTGRES_RAW_TABLE_NAME"],
            metadata,
            Column("repository_id", BigInteger),
            Column("name", Text),
            Column("full_name", Text),
            Column("owner", Text),
            Column("language", Text),
            Column("stargazers_count", BigInteger),
            Column("forks_count", BigInteger),
            Column("created_at", Text),
            Column("updated_at", Text),
            Column("license", Text),
            Column("ingested_at", Text),
            Column("page", BigInteger),
        )

        engine = create_engine(POSTGRES_URL)
        try:
            metadata.create_all(engine, checkfirst=True)
        finally:
            engine.dispose()

    @task
    def copy_bronze_postgresql(file_info: dict):
        TABLE_NAME = os.getenv("POSTGRES_RAW_TABLE_NAME")
            
        if TABLE_NAME is None:
                logger.error("POSTGRES_RAW_TABLE_NAME env value was not found")
                raise ValueError("POSTGRES_RAW_TABLE_NAME environment variable is not set.")
        
        file = Path(file_info["file_path"])
        logger.info(f"processing parquet file {file.absolute()}")
        df_ing = pl.read_parquet(file.absolute())
        
        df_ing = transform_before_db(df_ing)

        df_ing.write_database(
                connection=POSTGRES_URL,
                table_name=TABLE_NAME,
                if_table_exists="append",
                engine='sqlalchemy'
        )

    @task
    def build_extract_configs() -> list[dict]:
        return [
            {
                "q": TEST_QUERY,
                "per_page": 10,
                "page": page,
            }
            for page in range(1, PAGES_TO_FETCH + 1)
        ]


    extract_configs = build_extract_configs()

    bronze_files = extract_and_save_bronze.expand_kwargs(
        extract_configs
    )

    bucket_ready = ensure_minio_bucket()
    uploads = upload_bronze_to_minio.expand(file_info=bronze_files)

    bucket_ready >> uploads
    
    ensure_raw_table() >> copy_bronze_postgresql.expand(file_info=bronze_files)

github_extract_pipeline()
