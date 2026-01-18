with source as (
    select * from {{ source('raw', 'yolo_detections') }}
)

select
    message_id,
    channel_name,
    image_path,
    detected_objects,
    avg_confidence,
    image_category
from source