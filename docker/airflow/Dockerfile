FROM apache/airflow:3.3.2-python3.14

USER airflow
WORKDIR /opt/airflow

COPY pyproject.toml uv.lock README.md ./
COPY src/ ./src/

# RUN test -f /opt/airflow/src/github_analytics_platform/__init__.py

RUN pip install --no-cache-dir uv && \
    uv pip install --no-cache -p /home/airflow/.local/bin/python .