from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class VideoBase(BaseModel):
    title: str
    type: str
    url: str
    duration: Optional[str] = None
    thumbnail_url: Optional[str] = None

class VideoCreate(VideoBase):
    pass

class VideoLinkCreate(BaseModel):
    title: str
    url: str
    duration: Optional[str] = None

class VideoResponse(VideoBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
