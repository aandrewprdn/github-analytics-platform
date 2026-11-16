"""Assets shared between DAGs.

The extract DAG emits RAW_GITHUB_REPOSITORIES after loading Postgres;
the dbt DAG is scheduled on it, so transformations run right after new raw data lands.
"""

from airflow.sdk import Asset

RAW_GITHUB_REPOSITORIES = Asset(name="raw_github_repositories", group="github")
