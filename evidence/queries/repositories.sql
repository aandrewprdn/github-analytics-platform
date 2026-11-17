-- One row per repository (latest snapshot), enriched for the dashboards.
-- Shared by several pages: reference it as data="/queries/repositories".
select
    repository_id,
    full_name,
    owner_login,
    language_group,
    license_name,
    stargazers_count,
    forks_count,
    forks_to_stars_ratio,
    created_at,
    extract(year from created_at)::int as created_year,
    repository_age_days,
    'https://github.com/' || full_name as github_url
from analytics_marts.dim_repositories
