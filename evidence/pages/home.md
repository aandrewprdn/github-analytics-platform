---
title: Overview
sidebar_position: 1
---

# GitHub Repositories Overview

Repositories returned by the GitHub search query in the `github_extract_pipeline` Airflow DAG.
All numbers come from the dbt marts (`analytics_marts`), which are rebuilt after every pipeline
run, and each repository is counted once using its latest snapshot.

```sql kpis
select
    count(*) as repositories,
    sum(stargazers_count) as stars,
    sum(forks_count) as forks,
    percentile_cont(0.5) within group (order by stargazers_count) as median_stars
from analytics_marts.dim_repositories
```

{% row %}
    {% big_value data="kpis" value="sum(repositories)" title="Repositories" fmt="num0" /%}
    {% big_value data="kpis" value="sum(stars)" title="Total stars" fmt="num0" /%}
    {% big_value data="kpis" value="sum(forks)" title="Total forks" fmt="num0" /%}
    {% big_value data="kpis" value="sum(median_stars)" title="Median stars per repo" fmt="num0" info="Half of the repositories have fewer stars than this. Much lower than the average, because a few popular repositories hold most of the stars." /%}
{% /row %}

## Most popular repositories

{% row %}
    {% horizontal_bar_chart
        data="/queries/repositories"
        x="full_name"
        y="sum(stargazers_count)"
        order="sum(stargazers_count) desc"
        limit=10
        title="Top 10 repositories by stars"
    /%}
    {% horizontal_bar_chart
        data="/queries/repositories"
        x="owner_login"
        y="sum(stargazers_count)"
        order="sum(stargazers_count) desc"
        limit=10
        title="Top 10 owners by total stars"
    /%}
{% /row %}

## When were these repositories created?

{% row %}
    {% bar_chart
        data="/queries/repositories"
        x="created_at"
        y="count(*)"
        date_grain="year"
        title="Repositories created per year"
    /%}
    {% line_chart
        data="analytics_marts.agg_repository_creation_monthly"
        x="creation_month"
        y="sum(total_stars)"
        date_grain="year"
        title="Stars by creation year"
        subtitle="Current stars of repositories, grouped by the year they were created"
    /%}
{% /row %}

## Licenses and languages

{% row %}
    {% bar_chart
        data="/queries/repositories"
        x="license_name"
        y="count(*)"
        order="count(*) desc"
        title="Repositories by license"
    /%}
    {% bar_chart
        data="analytics_marts.agg_language_popularity"
        x="language_group"
        y="sum(repository_count)"
        order="sum(repository_count) desc"
        title="Repositories by language"
        subtitle="Driven by the search query; broaden it to compare languages"
    /%}
{% /row %}
