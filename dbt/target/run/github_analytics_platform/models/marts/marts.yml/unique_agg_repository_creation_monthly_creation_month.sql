
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

select
    creation_month as unique_field,
    count(*) as n_records

from "github_analytics"."zz_check_marts"."agg_repository_creation_monthly"
where creation_month is not null
group by creation_month
having count(*) > 1



  
  
      
    ) dbt_internal_test