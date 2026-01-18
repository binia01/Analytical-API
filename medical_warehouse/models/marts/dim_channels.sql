with stg_messages as (
    select * from {{ ref('stg_telegram_messages') }}
),

channel_stats as (
    select
        channel_name,
        min(channel_title) as channel_title,
        min(message_date) as first_post_date,
        max(message_date) as last_post_date,
        count(*) as total_posts,
        avg(views) as avg_views
    from stg_messages
    group by channel_name
)

select
    -- Surrogate Key (hashing channel name)
    md5(channel_name) as channel_key,
    channel_name,
    channel_title,
    -- Business Logic for Channel Type
    case 
        when channel_name ilike '%cosmetics%' then 'Cosmetics'
        when channel_name ilike '%pharma%' then 'Pharmaceuticals'
        when channel_name ilike '%chemed%' then 'Medical Device'
        else 'General Health'
    end as channel_type,
    first_post_date,
    last_post_date,
    total_posts,
    round(avg_views, 2) as avg_views
from channel_stats