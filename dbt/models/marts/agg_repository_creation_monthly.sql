select
    date_trunc('month', created_at)::date as creation_month,
    count(*) as repository_count,
    sum(stargazers_count) as total_stars,
    round(avg(stargazers_count)::numeric, 2) as average_stars,
    sum(forks_count) as total_forks,
    count(*) filter (where license_name = 'No license') as repositories_without_license,
    count(*) filter (where language_group = 'Unknown') as repositories_without_language
from {{ ref('dim_repositories') }}
where created_at is not null
group by 1
