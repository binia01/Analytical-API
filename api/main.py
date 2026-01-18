from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
from . import database, schemas

app = FastAPI(
    title="Kara Solutions Medical Data API",
    description="Analytical API for Ethiopian Medical Telegram Channels",
    version="1.0.0"
)

# Endpoint 1: Top Products (Keywords)
@app.get("/api/reports/top-products", response_model=List[schemas.TopProduct])
def get_top_products(limit: int = 10, db: Session = Depends(database.get_db)):
    """
    Returns the most frequently mentioned words, excluding numbers and common generic terms.
    """
    query = text("""
        SELECT word, ndoc
        FROM ts_stat('SELECT to_tsvector(''english'', message_text) FROM fct_messages')
        WHERE length(word) > 2          -- Remove short words like "2", "6"
        AND word ~ '^[a-z]+$'           -- Keep only letters (removes '500', '100mg')
        AND word NOT IN (               -- Remove generic Telegram spam words
            'telegram', 'channel', 'contact', 'price', 'call', 'address', 
            'phone', 'birr', 'etb', 'available', 'delivery'
        )
        ORDER BY ndoc DESC
        LIMIT :limit
    """)
    
    result = db.execute(query, {"limit": limit}).fetchall()
    
    return [{"word": row.word, "frequency": row.ndoc} for row in result]


# Endpoint 2: Channel Activity
@app.get("/api/channels/{channel_name}/activity",
         response_model=List[schemas.ChannelActivity])
def get_channel_activity(channel_name: str, db: Session = Depends(database.get_db)):
    """
    Returns daily posting volume and view counts for a specific channel.
    """
    # Join Fact Messages with Date Dimension
    query = text("""
        SELECT 
            d.full_date as date,
            COUNT(m.message_id) as post_count,
            COALESCE(SUM(m.view_count), 0) as total_views
        FROM fct_messages m
        JOIN dim_channels c ON m.channel_key = c.channel_key
        JOIN dim_dates d ON m.date_key = d.date_key
        WHERE c.channel_name = :channel_name
        GROUP BY d.full_date
        ORDER BY d.full_date DESC
    """)
    
    result = db.execute(query, {"channel_name": channel_name}).fetchall()
    
    if not result:
        raise HTTPException(status_code=404, detail="Channel not found or no data available")
        
    return [{"date": row.date, "post_count": row.post_count, "total_views": row.total_views} for row in result]

# --- Endpoint 3: Message Search ---
@app.get("/api/search/messages", response_model=List[schemas.MessageResponse])
def search_messages(
    query: str = Query(..., min_length=3), 
    limit: int = 20, 
    db: Session = Depends(database.get_db)
):
    """
    Full-text search for specific medical products (e.g., 'Paracetamol').
    """
    sql_query = text("""
        SELECT 
            m.message_id as id,
            c.channel_name,
            d.full_date as date,
            m.message_text as text,
            m.view_count as views
        FROM fct_messages m
        JOIN dim_channels c ON m.channel_key = c.channel_key
        JOIN dim_dates d ON m.date_key = d.date_key
        WHERE m.message_text ILIKE :search_term
        ORDER BY m.view_count DESC
        LIMIT :limit
    """)
    
    result = db.execute(sql_query, {"search_term": f"%{query}%", "limit": limit}).fetchall()
    
    return [
        {
            "id": row.id,
            "channel_name": row.channel_name,
            "date": row.date,
            "text": row.text,
            "views": row.views
        } 
        for row in result
    ]

# --- Endpoint 4: Visual Content Stats (Task 3 Integration) ---
@app.get("/api/reports/visual-content", response_model=List[schemas.VisualStats])
def get_visual_stats(db: Session = Depends(database.get_db)):
    """
    Returns engagement stats based on YOLO image classification.
    """
    query = text("""
        SELECT 
            image_category as category,
            AVG(view_count) as avg_views,
            COUNT(*) as total_images
        FROM fct_image_detections
        GROUP BY image_category
        ORDER BY avg_views DESC
    """)
    
    try:
        result = db.execute(query).fetchall()
        return [
            {
                "category": row.category, 
                "avg_views": round(row.avg_views, 2) if row.avg_views else 0, 
                "total_images": row.total_images
            } 
            for row in result
        ]
    except Exception as e:
        # Graceful fallback if Task 3 table doesn't exist yet
        raise HTTPException(status_code=500, detail="Visual stats not available yet.")