from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from database import Base

class GalleryImage(Base):
    __tablename__ = "gallery_images"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    filepath = Column(String(500), nullable=False)
    title = Column(String(200))
    description = Column(String(500))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
