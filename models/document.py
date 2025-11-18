from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, LargeBinary, BigInteger
from sqlalchemy.sql import func
from database import Base

class UserDocument(Base):
    __tablename__ = "user_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255))
    file_type = Column(String(100))
    file_size = Column(BigInteger)
    
    file_path = Column(String(500))
    file_data = Column(LargeBinary)
    
    category = Column(String(100))
    description = Column(String(500))
    
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
