
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select creation_month
from "github_analytics"."zz_check_marts"."agg_repository_creation_monthly"
where creation_month is null



  
  
      
    ) dbt_internal_test