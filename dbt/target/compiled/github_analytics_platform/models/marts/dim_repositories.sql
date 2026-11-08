with ranked_repositories as (
    select
        *,
        row_number() over (
            partition by repository_id
            order by ingested_at desc nulls last, updated_at desc nulls last
        ) as record_rank
    from "github_analytics"."zz_check_staging"."stg_github_repositories"
),

latest_repositories as (
    select *
    from ranked_repositories
    where record_rank = 1
)

select
    repository_id,
    name,
    full_name,
    owner ->> 'login' as owner_login,
    language,
    coalesce(language, 'Unknown') as language_group,
    coalesce((license ->> 'spdx_id'), (license ->> 'name'), 'No license') as license_name,
    stargazers_count,
    forks_count,
    case when stargazers_count > 0 then round(forks_count::numeric / stargazers_count, 4) else null end as forks_to_stars_ratio,
    created_at,
    updated_at,
    ingested_at,
    (current_date - created_at::date) as repository_age_days
from latest_repositories