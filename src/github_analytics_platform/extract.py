from datetime import datetime
import polars as pl
import logging
from github_analytics_platform.github_client import GithubClient
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

INGESTION_PATH = "/home/andrii/Developing/data-engineer/github-analytics-platform/ingestions/github-analytics/bronze/github/repositories"

def save_json_to_parquet_local_file(json_data: dict, output_file: str):
    """
    Save JSON data to a Parquet file using Polars.

    Args:
        json_data (dict): The JSON data to be saved.
        output_file (str): The path to the output Parquet file.
    """
    logger.info(f"Saving JSON data to Parquet file: {output_file}")
    df = pl.DataFrame(json_data)
    df.write_parquet(output_file, mkdir=True)

def collect_and_save_github_data(q: str, per_page: int = 10, pages_to_fetch: int = 1):
    """
    Collect GitHub repository data and save it to a Parquet file.

    Args:
        q (str): The search query for GitHub repositories.
        per_page (int): Number of results per page (default is 10).
        pages_to_fetch (int): Number of pages to fetch (default is 1).
    """
    with GithubClient() as client:
        pages_data_iter = client.iter_repos(q=q, per_page=per_page, pages_to_fetch=pages_to_fetch)

        for page_data in pages_data_iter:
            items = page_data.get("items", [])

            ingestion_date = datetime.fromisoformat(page_data["_metadata"]["ingested_at"]).date().isoformat()
            page_num = page_data["_metadata"].get("page", 1)
            
            save_json_to_parquet_local_file(items, f"{INGESTION_PATH}/{ingestion_date}/page_{page_num}.parquet")


if __name__ == "__main__":
    collect_and_save_github_data(
        q="dataengineer language:python",
        per_page=10,
        pages_to_fetch=5
    )