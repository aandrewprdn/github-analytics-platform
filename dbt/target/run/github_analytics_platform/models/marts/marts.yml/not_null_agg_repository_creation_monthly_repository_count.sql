
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select repository_count
from "github_analytics"."zz_check_marts"."agg_repository_creation_monthly"
where repository_count is null



  
  
      
    ) dbt_internal_test