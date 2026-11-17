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

# --- Evidence dashboards (runs in Docker, see the `evidence` service) ---
ENV := set -a && . ./.env && set +a

.PHONY: evidence-setup evidence-up evidence-validate evidence-logs

evidence-setup:  ## create/refresh the read-only Postgres role used by Evidence
	@$(ENV) && docker compose exec -T postgres psql -q -U "$$POSTGRES_USER" -d "$$POSTGRES_DB" \
		-v dbname="$$POSTGRES_DB" -v reader_user="$$EVIDENCE_DB_USER" \
		-v reader_password="$$EVIDENCE_DB_PASSWORD" -v marts_schema=analytics_marts \
		-f - < docker/postgres/create_evidence_reader.sql

evidence-up:     ## start the dashboards on http://localhost:3000
	docker compose up -d evidence

evidence-validate:  ## check page syntax and queries
	docker compose run --rm --no-deps evidence evidence validate

evidence-logs:
	docker compose logs -f evidence
