# dbt runs locally via uv in its own isolated env (dbt/.venv), reading credentials from .env.
DBT := cd dbt && uv run --env-file ../.env dbt

.PHONY: dbt-setup dbt-debug dbt-build dbt-run dbt-test dbt-docs dbt-clean

dbt-setup:   ## install dbt + packages
	cd dbt && uv sync && uv run dbt deps

dbt-debug:   ## check connection/profile
	$(DBT) debug

dbt-build:   ## run + test all models (pass s=<selector> to narrow)
	$(DBT) build $(if $(s),--select $(s))

dbt-run:
	$(DBT) run $(if $(s),--select $(s))

dbt-test:
	$(DBT) test $(if $(s),--select $(s))

dbt-docs:    ## generate and serve docs on :8081
	$(DBT) docs generate && $(DBT) docs serve --port 8081

dbt-clean:
	$(DBT) clean
