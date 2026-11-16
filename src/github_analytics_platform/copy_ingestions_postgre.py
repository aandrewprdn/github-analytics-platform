import polars as pl
import pathlib
import json
import logging
import os

from sqlalchemy import Engine, MetaData, Table, delete, func, insert

logger = logging.getLogger(__name__)


def replace_page_in_db(df: pl.DataFrame, table_name: str, engine: Engine) -> None:
    """Idempotently load one bronze page into the raw table.

    Bronze is stored as one file per (ingestion date, page) and a same-day re-run
    overwrites that file, so the raw table mirrors it: delete the rows of this
    (day, page) and insert the new ones in a single transaction. Retries and
    re-runs replace data instead of appending duplicates; a new day adds a new
    snapshot (deduplicated to the latest version in dbt's dim_repositories).

    Args:
        df (pl.DataFrame): output of transform_before_db for exactly one page
        table_name (str): raw table name
        engine (Engine): SQLAlchemy engine for the target database
    """
    if df.is_empty():
        logger.info("Nothing to load: page is empty")
        return

    # The key comes from the data itself, so it always matches what is inserted.
    ingestion_date = df["ingested_at"][0][:10]  # ISO timestamp -> "YYYY-MM-DD"
    page = int(df["page"][0])

    with engine.begin() as conn:  # one transaction: commit both or roll back both
        table = Table(table_name, MetaData(), autoload_with=conn)
        deleted = conn.execute(
            delete(table).where(
                func.left(table.c.ingested_at, 10) == ingestion_date,
                table.c.page == page,
            )
        ).rowcount
        conn.execute(insert(table), df.to_dicts())

    logger.info(
        "Loaded %s rows into %s for ingestion_date=%s page=%s (replaced %s existing rows)",
        df.height, table_name, ingestion_date, page, deleted,
    )

def transform_before_db(df_ing: pl.DataFrame) -> pl.DataFrame:
    """Omits unnessesary columns and converts nested structs to jsonb

    Args:
        df_ing (pl.DataFrame): DataFrame to transform

    Returns:
        pl.DataFrame: transformed DataFrame
    """
    ingested_at = df_ing['_metadata'][0]['ingested_at']
    page = df_ing['_metadata'][0]['page']

    df_ing = df_ing.select([
        pl.col("id").alias("repository_id"),
        "name",
        "full_name",
        "owner",
        "language",
        "stargazers_count",
        "forks_count",
        "created_at",
        "updated_at",
        "license",
        "ingested_at",
    ])

    df_ing = df_ing.with_columns([
        pl.col("owner").map_elements(json.dumps, return_dtype=pl.String),
        pl.col("license").map_elements(
            lambda x: json.dumps(x) if x is not None else None,
            return_dtype=pl.String),
    ])

    df_ing = df_ing.with_columns([
        pl.lit(ingested_at).alias("ingested_at"),
        pl.lit(page).alias("page")
    ])

    return df_ing


def copy_ingestions_to_db(ingestion_path: pathlib.Path):
    TABLE_NAME = os.getenv("POSTGRES_RAW_TABLE_NAME")
    
    if TABLE_NAME is None:
        logger.error("POSTGRES_RAW_TABLE_NAME env value was not found")
        raise ValueError("POSTGRES_RAW_TABLE_NAME environment variable is not set.")

    for file in ingestion_path.rglob("*.parquet"):
        logger.info(f"processing parquet file {file.absolute()}")
        df_ing = pl.read_parquet(file.absolute())

        df_ing = transform_before_db(df_ing)

        connection_string = f"postgresql+psycopg://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:5432/{os.getenv('POSTGRES_DB')}"
        logger.info(f"writing to database {connection_string}")
        df_ing.write_database(
            connection=connection_string,
            table_name=TABLE_NAME,
            if_table_exists="append",
            engine='sqlalchemy'
        )
