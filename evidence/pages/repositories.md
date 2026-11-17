---
title: Repository Explorer
sidebar_position: 2
---

# Repository Explorer

Search and filter every repository in the latest snapshot. Click a row to open it on GitHub.

{% row %}
    {% dropdown
        id="license"
        data="/queries/repositories"
        value_column="license_name"
        title="License"
    /%}
    {% dropdown
        id="owner"
        data="/queries/repositories"
        value_column="owner_login"
        title="Owner"
    /%}
{% /row %}

{% row %}
    {% big_value data="/queries/repositories" value="count(*)" title="Repositories" fmt="num0" filters=["license", "owner"] /%}
    {% big_value data="/queries/repositories" value="sum(stargazers_count)" title="Stars" fmt="num0" filters=["license", "owner"] /%}
    {% big_value data="/queries/repositories" value="avg(forks_to_stars_ratio)" title="Avg forks per star" fmt="num2" filters=["license", "owner"] info="Forks divided by stars, averaged over repositories with at least one star. Higher means people copy the code rather than just bookmark it." /%}
{% /row %}

{% table
    data="/queries/repositories"
    filters=["license", "owner"]
    search=true
    subtotals=false
    link="github_url"
    order="sum(stargazers_count) desc"
%}
    {% dimension value="full_name" title="Repository" /%}
    {% dimension value="owner_login" title="Owner" /%}
    {% dimension value="license_name" title="License" /%}
    {% dimension value="created_at" title="Created" fmt="longdate" /%}
    {% dimension value="github_url" hide=true /%}
    {% measure value="sum(stargazers_count)" title="Stars" fmt="num0" /%}
    {% measure value="sum(forks_count)" title="Forks" fmt="num0" /%}
{% /table %}
