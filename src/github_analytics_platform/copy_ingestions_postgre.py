import polars as pl
import pathlib
import json
import logging
import os

logger = logging.getLogger(__name__)

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

        logger.info(f"writing to database {f"postgresql+psycopg://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:5432/{os.getenv('POSTGRES_DB')}"}")
        df_ing.write_database(
            connection=f"postgresql+psycopg://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:5432/{os.getenv('POSTGRES_DB')}",
            table_name=TABLE_NAME,
            if_table_exists="append",
            engine='sqlalchemy'
        )

# if __name__ == "__main__":
#     from dotenv import load_dotenv
#     load_dotenv()
    
#     local_ingestions_path = os.getenv("LOCAL_INGESTIONS_PATH")

#     if local_ingestions_path :
#         local_ingestions_path = pathlib.Path(local_ingestions_path)  
#     else:
#         local_ingestions_path = pathlib.Path("ingestions/github-analytics/bronze/github/repositories")
    
#     copy_ingestions_to_db(local_ingestions_path)