
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

select
    language_group as unique_field,
    count(*) as n_records

from "github_analytics"."zz_check_marts"."agg_language_popularity"
where language_group is not null
group by language_group
having count(*) > 1



  
  
      
    ) dbt_internal_test