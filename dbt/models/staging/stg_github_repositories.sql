with source as (
    select *
    from {{ source('github_ingestion', 'raw_repositories') }}
),

renamed as (
    select
        repository_id::bigint as repository_id,
        name,
        full_name,
        owner::jsonb as owner,
        language,
        stargazers_count::bigint as stargazers_count,
        forks_count::bigint as forks_count,
        created_at::timestamptz as created_at,
        updated_at::timestamptz as updated_at,
        license::jsonb as license,
        ingested_at::timestamptz as ingested_at,
        page::integer as page
    from source
)

select * from renamed
