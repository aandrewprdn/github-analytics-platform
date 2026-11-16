"""Run the dbt project with Astronomer Cosmos.

Cosmos renders every dbt model as its own Airflow task (plus a test task after it),
following the dbt lineage graph. The DAG is triggered by the raw-data asset that
github_extract_pipeline emits, so there is no separate cron schedule to keep in sync.
"""

from datetime import datetime
from pathlib import Path

from cosmos import DbtDag, ExecutionConfig, ProfileConfig, ProjectConfig, RenderConfig
from cosmos.constants import InvocationMode, LoadMode

from common.assets import RAW_GITHUB_REPOSITORIES

DBT_PROJECT_DIR = Path("/opt/airflow/dbt_project")
# dbt is installed in its own virtualenv (see docker/airflow/Dockerfile) so its
# dependency pins never clash with Airflow's.
DBT_EXECUTABLE = "/home/airflow/dbt-venv/bin/dbt"

profile_config = ProfileConfig(
    profile_name="github_analytics_platform",
    target_name="dev",
    # Reuses dbt/profiles.yml, which reads POSTGRES_* and DBT_HOST from the environment.
    profiles_yml_filepath=DBT_PROJECT_DIR / "profiles.yml",
)

github_dbt_transform = DbtDag(
    dag_id="github_dbt_transform",
    project_config=ProjectConfig(DBT_PROJECT_DIR),
    profile_config=profile_config,
    execution_config=ExecutionConfig(
        dbt_executable_path=DBT_EXECUTABLE,
        # Run dbt as a subprocess from its own venv instead of importing it into Airflow.
        invocation_mode=InvocationMode.SUBPROCESS,
    ),
    render_config=RenderConfig(
        load_method=LoadMode.DBT_LS,
        dbt_executable_path=DBT_EXECUTABLE,
        invocation_mode=InvocationMode.SUBPROCESS,
    ),
    schedule=[RAW_GITHUB_REPOSITORIES],
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    default_args={"retries": 1},
    tags=["github", "dbt"],
)
