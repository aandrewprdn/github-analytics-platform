FROM apache/airflow:3.3.2-python3.14

USER airflow
WORKDIR /opt/airflow

ENV UV_PYTHON_DOWNLOADS=never

RUN pip install --no-cache-dir uv

# dbt gets its own virtualenv, installed from dbt/uv.lock, so its pins never clash
# with Airflow's. Cosmos calls /home/airflow/dbt-venv/bin/dbt.
COPY dbt/pyproject.toml dbt/uv.lock /home/airflow/dbt-deps/
RUN UV_PROJECT_ENVIRONMENT=/home/airflow/dbt-venv \
    uv sync --frozen --no-install-project --no-dev --no-cache \
        --project /home/airflow/dbt-deps --python /usr/local/bin/python

COPY pyproject.toml uv.lock README.md ./
COPY src/ ./src/

# Project code + Cosmos go into Airflow's own environment.
RUN uv pip install --no-cache -p /home/airflow/.local/bin/python . "astronomer-cosmos==1.16.0"
