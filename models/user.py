from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(200))
    phone = Column(String(50))
    date_of_birth = Column(String(50))
    nationality = Column(String(100))
    
    # License Management (Admin Portal)
    license_active = Column(Boolean, default=True)
    license_type = Column(String(50), default="basic")
    license_expiry = Column(DateTime(timezone=True))
    
    # User folder path
    user_folder = Column(String(500))
    
    # Password (hashed)
    hashed_password = Column(String(255))
    
    # Experience (Customer Registration)
    experience_years = Column(Integer)
    previous_roles = Column(Text)
    skills = Column(Text)
    preferred_country = Column(String(100))
    preferred_city = Column(String(100))
    
    # CV
    cv_filename = Column(String(255))
    cv_path = Column(String(500))
    
    # Registration Status (Customer)
    current_step = Column(Integer, default=1)
    registration_status = Column(String(50), default="pending")
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))
    
    # Admin notes
    admin_notes = Column(Text)
