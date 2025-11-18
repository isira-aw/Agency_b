from sqlalchemy import Column, Integer, String, DateTime, Date, Boolean, Text
from sqlalchemy.sql import func
from database import Base

class CalendarEvent(Base):
    __tablename__ = "calendar_events"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    event_type = Column(String(100))
    
    event_date = Column(Date, nullable=False, index=True)
    event_time = Column(String(20))
    all_day = Column(Boolean, default=False)
    
    requires_notification = Column(Boolean, default=True)
    notification_count = Column(Integer, default=0)
    
    status = Column(String(50), default="active")
    reference_id = Column(Integer)
    reference_type = Column(String(50))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
