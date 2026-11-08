
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select repository_id
from "github_analytics"."zz_raw_check"."repositories_raw"
where repository_id is null



  
  
      
    ) dbt_internal_test