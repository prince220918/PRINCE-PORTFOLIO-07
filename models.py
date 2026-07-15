from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from database import Base

class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    type = Column(String, nullable=False) # 'local', 'youtube', 'instagram'
    url = Column(String, nullable=False)   # Local filepath (relative URL) or Youtube/Insta URL
    duration = Column(String, nullable=True) # e.g. "02:15"
    thumbnail_url = Column(String, nullable=True) # Scraped thumbnail for Instagram
    created_at = Column(DateTime, default=datetime.utcnow)
