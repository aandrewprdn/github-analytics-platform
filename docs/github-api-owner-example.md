# GitHub API: `owner` object

Example of the `owner` object returned for each item by the search endpoint
`https://api.github.com/search/repositories?q=<query>`. The ingestion stores it as JSON text in the
raw table, and the dbt model `stg_owner` unpacks it into typed columns with `jsonb_to_record`.

```json
"owner": {
    "login": "dtrupenn",
    "id": 872147,
    "node_id": "MDQ6VXNlcjg3MjE0Nw==",
    "avatar_url": "https://secure.gravatar.com/avatar/e7956084e75f239de85d3a31bc172ace?d=https://a248.e.akamai.net/assets.github.com%2Fimages%2Fgravatars%2Fgravatar-user-420.png",
    "gravatar_id": "",
    "url": "https://api.github.com/users/dtrupenn",
    "received_events_url": "https://api.github.com/users/dtrupenn/received_events",
    "type": "User",
    "html_url": "https://github.com/octocat",
    "followers_url": "https://api.github.com/users/octocat/followers",
    "following_url": "https://api.github.com/users/octocat/following{/other_user}",
    "gists_url": "https://api.github.com/users/octocat/gists{/gist_id}",
    "starred_url": "https://api.github.com/users/octocat/starred{/owner}{/repo}",
    "subscriptions_url": "https://api.github.com/users/octocat/subscriptions",
    "organizations_url": "https://api.github.com/users/octocat/orgs",
    "repos_url": "https://api.github.com/users/octocat/repos",
    "events_url": "https://api.github.com/users/octocat/events{/privacy}",
    "site_admin": true
}
```
