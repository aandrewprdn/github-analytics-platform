FROM apache/airflow:3.1.0-python3.13

USER airflow
WORKDIR /opt/airflow

COPY pyproject.toml uv.lock ./

RUN pip install --no-cache-dir uv psycopg[binary] && \
    uv sync --frozen --no-dev --no-install-project