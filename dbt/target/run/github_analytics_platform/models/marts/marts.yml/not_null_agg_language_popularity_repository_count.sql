
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select repository_count
from "github_analytics"."zz_check_marts"."agg_language_popularity"
where repository_count is null



  
  
      
    ) dbt_internal_test