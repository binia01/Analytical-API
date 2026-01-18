with detections as (
    select * from {{ ref('stg_yolo_detections') }}
),

messages as (
    select * from {{ ref('fct_messages') }}
),

channels as (
    select * from {{ ref('dim_channels') }}
),

dates as (
    select * from {{ ref('dim_dates') }}
)

select
    d.message_id,
    m.channel_key,
    m.date_key,
    d.image_category,
    d.detected_objects,
    d.avg_confidence,
    -- Bring in metrics for analysis
    m.view_count,
    m.forward_count
from detections d
left join messages m on d.message_id = m.message_id
-- We assume message_id is unique enough, or join on channel+id if needed