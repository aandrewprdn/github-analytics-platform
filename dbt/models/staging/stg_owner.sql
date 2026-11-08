with source as (
    select
        repository_id,
        owner,
        ingested_at
    from {{ source('github_ingestion', 'raw_repositories') }}
),

-- jsonb_to_record's column list must use the exact JSON keys with a type ("key type");
-- casts and renames happen in the select below.
renamed as (
    select
        source.repository_id::bigint as repository_id,
        source.ingested_at::timestamptz as ingested_at,
        owner_record.id as owner_id,
        owner_record.login as owner_login,
        owner_record.node_id as owner_node_id,
        owner_record."type" as owner_type,
        owner_record.site_admin as is_site_admin,
        owner_record.avatar_url,
        nullif(owner_record.gravatar_id, '') as gravatar_id,
        owner_record.html_url as owner_html_url,
        owner_record.url as owner_api_url,
        owner_record.followers_url,
        owner_record.subscriptions_url,
        owner_record.organizations_url,
        owner_record.repos_url,
        owner_record.received_events_url
    from source
    cross join lateral jsonb_to_record(source.owner::jsonb) as owner_record (
        id bigint,
        login text,
        node_id text,
        "type" text,
        site_admin boolean,
        avatar_url text,
        gravatar_id text,
        html_url text,
        url text,
        followers_url text,
        following_url text,
        gists_url text,
        starred_url text,
        subscriptions_url text,
        organizations_url text,
        repos_url text,
        events_url text,
        received_events_url text
    )
)

select * from renamed
