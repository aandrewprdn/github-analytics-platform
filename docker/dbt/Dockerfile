FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

# git is used by `dbt deps` for git-hosted packages and checked by `dbt debug`
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/dbt

# Install only dependencies from the lockfile; the project itself is bind-mounted at runtime.
COPY dbt/pyproject.toml dbt/uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

ENTRYPOINT ["dbt"]
CMD ["debug"]
