with source as (
    select * from {{ source('raw', 'telegram_messages') }}
),

cleaned as (
    select
        message_id,
        channel_name,
        -- Standardize text
        channel_title,
        message_text,
        -- Cast timestamp
        message_date::timestamp as message_date,
        -- Handle nulls
        coalesce(views, 0) as views,
        coalesce(forwards, 0) as forwards,
        -- Boolean flags
        case when has_media = 'true' then true else false end as has_media,
        image_path,
        -- Calculated field
        length(message_text) as message_length
    from source
    -- Filter garbage data
    where message_date is not null
)

select * from cleaned