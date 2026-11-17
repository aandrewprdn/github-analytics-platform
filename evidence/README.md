# Dashboards (Evidence)

The dashboards for this project are built with [Evidence](https://docs.evidence.dev):
*BI as code*. Each dashboard page is a Markdown file with SQL queries and chart
components. The pages live in git next to the dbt models and Airflow DAGs, so a
dashboard change is reviewed in a pull request like any other code.

```
GitHub API ─► Airflow ─► MinIO (bronze) ─► Postgres raw ─► dbt ─► analytics_marts ─► Evidence
                                                                   (tested tables)    (this folder)
```

Evidence only reads the **dbt marts** (`analytics_marts`). The marts are deduplicated
and tested, so every chart shows one row per repository, and the business logic
stays in dbt instead of being copied into dashboard SQL.

## Pages

| Page | File | What it shows |
|---|---|---|
| Overview | `pages/home.md` | Headline numbers, top repositories and owners, creation trend, licenses and languages |
| Repository Explorer | `pages/repositories.md` | License and owner filters, plus a searchable table; click a row to open the repo on GitHub |

## Project layout

```
evidence/
├── evidence.config.yaml    # project name and Evidence version
├── connection.yaml         # Postgres connection; only ${ENV_VAR} references, no secrets
├── pages/                  # one Markdown file = one page in the sidebar
│   ├── home.md
│   └── repositories.md
└── queries/
    └── repositories.sql    # shared query, used as data="/queries/repositories"
```

## Running it

Evidence runs as a Docker Compose service. Postgres must be running and the dbt marts
must be built.

```bash
make evidence-setup   # one-off: create the read-only Postgres role (safe to re-run)
make evidence-up      # start the dashboards → http://localhost:3000
make evidence-logs    # follow the server logs
make evidence-validate  # check page syntax and run every query against Postgres
```

The service runs `evidence dev`, so saved changes to a page appear in the browser
straight away. It listens on `127.0.0.1` only, because the dev server has no login.

## Security: read-only database user

Evidence connects as `evidence_reader`, not as the database owner. The role is created
by [`docker/postgres/create_evidence_reader.sql`](../docker/postgres/create_evidence_reader.sql)
and can only `SELECT` from `analytics_marts`. It has no access to the raw tables,
staging views or Airflow's tables, and it can't create or change anything. Default
privileges keep it working after dbt drops and recreates the mart tables.

Credentials come from `.env` (`EVIDENCE_DB_USER`, `EVIDENCE_DB_PASSWORD`) and reach
`connection.yaml` through `${VAR}` references, so the committed file holds no secrets.

## Writing pages

Pages are Markdown. Data comes either from a table name or from a named SQL block,
and components use Markdoc `{% ... /%}` tags. Queries run as **Postgres SQL** because
this project uses a direct connector.

````markdown
```sql top_repos
select full_name, stargazers_count
from analytics_marts.dim_repositories
order by stargazers_count desc
limit 10
```

{% horizontal_bar_chart data="top_repos" x="full_name" y="sum(stargazers_count)" /%}
````

Useful components: `big_value`, `bar_chart`, `horizontal_bar_chart`, `line_chart`,
`table` (with `dimension` / `measure` children), `dropdown` (filters), and `row` /
`stack` for layout. Component reference: https://docs.evidence.dev/components

> Evidence's syntax changed in 2026 (Markdoc tags instead of `<BarChart>` Svelte
> components, plus a standalone CLI instead of `npm run dev`). Older tutorials and
> AI answers often show the old syntax; check the docs above.

## Optional: run the CLI on your machine

Docker is enough for everything above. If you'd rather run Evidence natively, install
the CLI (`curl -fsSL https://evidence.studio/install.sh | sh`), export the
`EVIDENCE_DB_*` variables with `EVIDENCE_DB_HOST=localhost`, and run `evidence dev`
inside this folder. Stop the Docker service first, since both use port 3000.

## Sharing it publicly

Evidence doesn't produce a static site, so it can't go on GitHub Pages. A self-hosted
deployment is a small server (`evidencedev/serve` image) that queries Postgres live, so
it needs a database reachable from the internet. For a portfolio, the practical options are:

1. **Screenshots or a short GIF** of the pages in the main README (no infrastructure needed).
2. **Hosted demo:** put the marts in a free managed Postgres (for example Neon), then deploy
   this folder with the `evidencedev/serve` image to Render or Fly.io, with HTTP Basic Auth
   or a read-only demo user.
