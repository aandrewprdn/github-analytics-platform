
    
    

select
    repository_id as unique_field,
    count(*) as n_records

from "github_analytics"."zz_check_marts"."dim_repositories"
where repository_id is not null
group by repository_id
having count(*) > 1


