import io
import logging
import os
from datetime import datetime

import polars as pl
from airflow.sdk import dag, task
from airflow.sdk.exceptions import AirflowSkipException
from sqlalchemy import URL, BigInteger, Column, MetaData, Table, Text, create_engine

from github_analytics_platform.copy_ingestions_postgre import replace_page_in_db, transform_before_db
from github_analytics_platform.github_client import GithubClient
from github_analytics_platform.minio_client import MinioClient

from common.assets import RAW_GITHUB_REPOSITORIES

# Airflow configures logging itself; calling logging.basicConfig here would
# override it for the whole DAG processor on every parse.
logger = logging.getLogger(__name__)


TEST_QUERY = "dataengineer language:python"
PAGES_TO_FETCH = 10


def postgres_url() -> URL:
    """Build the URL at run time; URL.create escapes special characters in the password."""
    return URL.create(
        "postgresql+psycopg",
        username=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        host=os.environ["POSTGRES_HOST"],
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        database=os.environ["POSTGRES_DB"],
    )


@dag("github_extract_pipeline")
def github_extract_pipeline():

    @task
    def extract_and_save_bronze(q: str, per_page: int = 10, page: int = 1) -> dict:
        """
        Fetch one page of GitHub search results and write it to MinIO as Parquet.

        The Parquet file is serialized into an in-memory buffer and uploaded directly,
        so nothing touches the local filesystem and any worker can run the task.

        Args:
            q (str): The search query for GitHub repositories.
            per_page (int): Number of results per page (default is 10).
            page (int): The page number to fetch (default is 1).

        Returns:
            metadata of the written page, e.g.
            {
                "page": 1,
                "ingestion_date": "2026-09-05",
                "object_key": "<MINIO_BASE_KEY>/ingestion_date=2026-09-05/page_1.parquet",
                "records": 10
            }
        """
        with GithubClient() as client:
            page_data = client.search_repos(q=q, per_page=per_page, page=page)

        # Pages past the last search result come back empty; skipping them
        # also skips this page's copy task instead of failing it.
        if not page_data.get("items"):
            raise AirflowSkipException(f"Page {page} returned no repositories")

        df = pl.DataFrame(page_data["items"]).with_columns(
            pl.lit(page_data["_metadata"]).alias("_metadata"),
        )

        ingestion_date = datetime.fromisoformat(page_data["_metadata"]["ingested_at"]).date().isoformat()
        page_num = page_data["_metadata"].get("page", 1)

        buffer = io.BytesIO()
        df.write_parquet(buffer)

        minio = MinioClient()
        # One object per (day, page): a same-day re-run overwrites it, and the
        # Postgres load mirrors that (see replace_page_in_db).
        object_key = f"{minio.base_key}/ingestion_date={ingestion_date}/page_{page_num}.parquet"
        minio.put_bytes(object_key, buffer.getvalue(), content_type="application/vnd.apache.parquet")

        return {
            "page": page,
            "ingestion_date": ingestion_date,
            "object_key": object_key,
            "records": df.height,
        }

    @task
    def ensure_minio_bucket():
        client = MinioClient()
        client.ensure_bucket()

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

        engine = create_engine(postgres_url())
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

        # MinIO is the source of truth for bronze: read the object straight into memory.
        object_key = file_info["object_key"]
        df_ing = pl.read_parquet(io.BytesIO(MinioClient().read_bytes(object_key)))
        logger.info("Read %s rows from %s", df_ing.height, object_key)

        df_ing = transform_before_db(df_ing)

        # Delete + insert of this (day, page) in one transaction: safe to retry/re-run.
        engine = create_engine(postgres_url())
        try:
            replace_page_in_db(df_ing, TABLE_NAME, engine)
        finally:
            engine.dispose()

    # A single, non-mapped task emits the asset once per run (mapped copy tasks would
    # emit one event per page). "none_failed" lets it run when empty pages were skipped.
    @task(outlets=[RAW_GITHUB_REPOSITORIES], trigger_rule="none_failed")
    def mark_raw_loaded():
        logger.info("Raw repositories loaded; emitting asset to trigger dbt")

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

    bronze_files = extract_and_save_bronze.expand_kwargs(extract_configs)
    ensure_minio_bucket() >> bronze_files

    # Expanding over the extract output links the tasks page by page: page i is copied
    # as soon as page i is in MinIO, and a skipped page doesn't block the others.
    raw_loads = copy_bronze_postgresql.expand(file_info=bronze_files)
    ensure_raw_table() >> raw_loads >> mark_raw_loaded()


github_extract_pipeline()
