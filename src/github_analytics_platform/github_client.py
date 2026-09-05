import requests
from requests.exceptions import ConnectionError, Timeout
from datetime import datetime, timezone
import os
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, before_sleep_log


logger = logging.getLogger(__name__)

class GithubClient:
    def __init__(self):
        self.token = os.getenv("GITHUB_API_TOKEN")
        if self.token is None:
            raise ValueError("GitHub API token is not set in the environment variables.")

        self.base_url = "https://api.github.com/search/repositories"
        self.session = requests.Session()
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
        }

        logger.debug("GithubClient initialized")

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=1, max=16),
        retry=retry_if_exception_type((ConnectionError, Timeout)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def search_repos(self, q: str, sort: str = "stars", order: str = "desc", per_page: int = 100, page: int = 1) -> dict:
        """
        Search GitHub repositories based on the provided query.

        Args:
            q (str): The search query.
            sort (str): The sorting criteria (default is "stars").
            order (str): The sorting order (default is "desc").
            per_page (int): Number of results per page (default is 100).
            page (int): Page number to fetch (default is 1).
        """
        logger.info(
            f"Searching GitHub repositories with query: {q}",
            extra={"per_page": per_page, "page": page, "sort": sort, "order": order}
        )

        response = self.session.get(self.base_url, 
                                    headers=self.headers,
                                    params={"q": q, "per_page": per_page, "page": page, "sort": sort, "order": order},
                                    timeout=10)

        if response.status_code >= 500:
            response.raise_for_status()
        elif response.status_code == 403 and response.headers["X-RateLimit-Remaining"] == "0":
            logger.warning(f"GitHub API rate limit exceeded for query: {q}")
            raise requests.HTTPError(f"GitHub API returned {response.status_code}")

        response.raise_for_status()
        
        data = response.json()

        ingested_at = datetime.now(timezone.utc).isoformat()
        for item in data.get("items", []):
            item["ingested_at"] = ingested_at

        data["_metadata"] = {
            "page": page,
            "per_page": per_page,
            "query": q,
            "ingested_at": ingested_at,
            "total_count": data.get("total_count"),
        }

        return data

    def iter_repos(self, q: str, sort: str = "stars", order: str = "desc", per_page: int = 100, pages_to_fetch: int = 1):
        page = 1
        while page <= pages_to_fetch:
            data = self.search_repos(q=q, sort=sort, order=order, per_page=per_page, page=page)
            if not data.get("items", []):
                break
            yield data
            page += 1

    def close(self):
        self.session.close()
        logger.debug("GithubClient session closed")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

