from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime

class MessageResponse(BaseModel):
    id: int
    channel_name: str
    date: date
    text: str
    views: int
    
    class Config:
        from_attributes = True

class ChannelActivity(BaseModel):
    date: date
    post_count: int
    total_views: int

class TopProduct(BaseModel):
    word: str
    frequency: int

class VisualStats(BaseModel):
    category: str
    avg_views: float
    total_images: int