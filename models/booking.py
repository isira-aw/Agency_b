from sqlalchemy import Column, Integer, String, DateTime, Date, Boolean, ForeignKey, Text
from sqlalchemy.sql import func
from database import Base

class Booking(Base):
    __tablename__ = "bookings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    
    # Booking Details
    name = Column(String(200), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=False)
    purpose = Column(String(500))
    title = Column(String(200))
    description = Column(Text)
    booking_type = Column(String(100))
    
    # Schedule
    date = Column(Date, nullable=False, index=True)
    time = Column(String(20), nullable=False)
    duration_minutes = Column(Integer, default=60)
    
    # Status
    status = Column(String(50), default="pending")
    
    # Notifications
    notification_sent = Column(Boolean, default=False)
    notification_date = Column(DateTime(timezone=True))
    reminder_sent = Column(Boolean, default=False)
    
    # Admin response
    admin_response = Column(Text)
    confirmed_by = Column(String(100))
    confirmed_at = Column(DateTime(timezone=True))
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
