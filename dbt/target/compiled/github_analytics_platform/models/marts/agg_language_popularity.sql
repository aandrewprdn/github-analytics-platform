select
    coalesce(language, 'Unknown') as language_group,
    count(*) as repository_count,
    sum(stargazers_count) as total_stars,
    round(avg(stargazers_count)::numeric, 2) as average_stars,
    percentile_cont(0.5) within group (order by stargazers_count) as median_stars,
    sum(forks_count) as total_forks,
    round(avg(forks_count)::numeric, 2) as average_forks,
    round(
        sum(stargazers_count)::numeric / nullif(sum(forks_count), 0),
        2
    ) as stars_per_fork
from "github_analytics"."zz_check_marts"."dim_repositories"
group by 1