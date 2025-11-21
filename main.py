
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import date, datetime
import os
import shutil
from pathlib import Path
from passlib.context import CryptContext
from fastapi.responses import StreamingResponse
from io import BytesIO
from models import UserDocument

from database import create_tables, get_db
from models import User, Booking, GalleryImage, UserDocument, Settings
from config import settings

# Initialize FastAPI
app = FastAPI(
    title="Unified Employee Agency API",
    version="3.0.0",
    description="Combined Customer Website + Admin Portal Backend"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
os.makedirs("static/cv", exist_ok=True)
os.makedirs("static/gallery", exist_ok=True)
os.makedirs(settings.USER_DATA_PATH, exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")

# Password hashing
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto"
)


# Create tables
create_tables()

# ==================== SCHEMAS ====================

# User Schemas
class UserRegisterCustomer(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[str] = None
    nationality: Optional[str] = None
    experience_years: Optional[int] = None
    previous_roles: Optional[str] = None
    skills: Optional[str] = None
    preferred_country: Optional[str] = None
    preferred_city: Optional[str] = None

class UserCreateAdmin(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    license_type: Optional[str] = "basic"

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    experience_years: Optional[int] = None
    previous_roles: Optional[str] = None
    skills: Optional[str] = None
    preferred_country: Optional[str] = None
    preferred_city: Optional[str] = None
    current_step: Optional[int] = None
    registration_status: Optional[str] = None
    license_active: Optional[bool] = None
    license_type: Optional[str] = None
    admin_notes: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    username: Optional[str] = None
    email: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    license_active: bool
    license_type: Optional[str] = None
    current_step: Optional[int] = None
    registration_status: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Booking Schemas
class BookingCreate(BaseModel):
    name: str
    email: EmailStr
    phone: str
    purpose: Optional[str] = None
    date: date
    time: str
    user_id: Optional[int] = None

class BookingUpdate(BaseModel):
    status: Optional[str] = None
    admin_response: Optional[str] = None

class BookingConfirm(BaseModel):
    status: str
    admin_response: Optional[str] = None
    confirmed_by: str

class BookingResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: str
    date: date
    time: str
    status: str
    user_id: Optional[int] = None
    admin_response: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Gallery Schema
class GalleryResponse(BaseModel):
    id: int
    filename: str
    filepath: str
    title: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Settings Schema
class SettingsUpdate(BaseModel):
    value: dict

class DocumentOut(BaseModel):
    id: int
    user_id: int
    filename: str
    category: str | None = None
    description: str | None = None
    uploaded_at: datetime
    download_url: str = ""  # Make it optional with default

    class Config:
        from_attributes = True


# ==================== CUSTOMER ROUTES ====================

@app.post("/api/customer/register/start", response_model=UserResponse)
def customer_register_start(user: UserRegisterCustomer, db: Session = Depends(get_db)):
    """Customer registration - Step 1"""
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    db_user = User(
        username=user.email.split('@')[0],  # Generate username from email
        email=user.email,
        full_name=f"{user.first_name or ''} {user.last_name or ''}".strip(),
        phone=user.phone,
        date_of_birth=user.date_of_birth,
        nationality=user.nationality,
        current_step=1,
        registration_status="in_progress",
        license_active=False  # Not active until admin approves
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Create user folder
    user_folder = Path(settings.USER_DATA_PATH) / f"user_{db_user.id}_{db_user.username}"
    user_folder.mkdir(parents=True, exist_ok=True)
    db_user.user_folder = str(user_folder)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@app.put("/api/customer/register/update/{id}", response_model=UserResponse)
def customer_register_update(id: int, user: UserUpdate, db: Session = Depends(get_db)):
    """Customer registration - Update steps"""
    db_user = db.query(User).filter(User.id == id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Registration not found")
    
    for key, value in user.model_dump(exclude_unset=True).items():
        setattr(db_user, key, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/api/customer/register/upload-cv/{id}")
async def customer_upload_cv(id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Customer upload CV (store directly in DB, not in local storage)"""
    
    db_user = db.query(User).filter(User.id == id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Registration not found")
    
    file_bytes = await file.read()

    document = UserDocument(
        user_id=id,
        filename=file.filename,
        original_filename=file.filename,
        file_type=file.content_type,
        file_size=len(file_bytes),
        file_path=None, 
        file_data=file_bytes,   
        category="cv",
        description="User CV"
    )

    db.add(document)
    db_user.current_step = 5
    db_user.registration_status = "submitted"
    db.commit()
    
    return {"message": "CV uploaded successfully", "filename": file.filename}

@app.post("/api/customer/register/payment/{id}")
async def customer_upload_payment(id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    
    db_user = db.query(User).filter(User.id == id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Registration not found")
    
    file_bytes = await file.read()

    document = UserDocument(
        user_id=id,
        filename=file.filename,
        original_filename=file.filename,
        file_type=file.content_type,
        file_size=len(file_bytes),
        file_path=None, 
        file_data=file_bytes,   
        category="payment",
        description="User Payment"
    )

    db.add(document)
    db_user.current_step = 5
    db_user.registration_status = "submitted"
    db.commit()
    
    return {"message": "payment uploaded successfully", "filename": file.filename}

@app.post("/api/customer/booking/create", response_model=BookingResponse)
def customer_create_booking(booking: BookingCreate, db: Session = Depends(get_db)):
    db_booking = Booking(**booking.model_dump())
    
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)

    return db_booking


@app.get("/api/customer/gallery", response_model=List[GalleryResponse])
def customer_get_gallery(db: Session = Depends(get_db)):
    """Get all gallery images"""
    return db.query(GalleryImage).all()

@app.get("/api/customer/settings/homepage")
def customer_get_homepage(db: Session = Depends(get_db)):
    """Get homepage content"""
    setting = db.query(Settings).filter(Settings.key == "homepage_content").first()
    if not setting:
        default = {
            "hero_title": "Your Gateway to European Employment",
            "hero_subtitle": "Connecting talented professionals with opportunities across EU",
            "about_text": "We specialize in placing skilled workers in positions throughout Europe.",
            "countries": ["Germany", "France", "Netherlands", "Belgium", "Austria"]
        }
        setting = Settings(key="homepage_content", value=default)
        db.add(setting)
        db.commit()
        db.refresh(setting)
    return setting

@app.get("/api/customer/settings/time-slots")
def customer_get_time_slots(db: Session = Depends(get_db)):
    """Get available time slots"""
    setting = db.query(Settings).filter(Settings.key == "time_slots").first()
    if not setting:
        default = {"slots": ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"]}
        setting = Settings(key="time_slots", value=default)
        db.add(setting)
        db.commit()
        db.refresh(setting)
    return setting

# ==================== ADMIN ROUTES ====================

# Users Management
@app.post("/api/admin/users", response_model=UserResponse)
def admin_create_user(user: UserCreateAdmin, db: Session = Depends(get_db)):
    """Admin create user"""
    existing = db.query(User).filter(
        (User.username == user.username) | (User.email == user.email)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username or email already exists")
    
    hashed_password = pwd_context.hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        license_type=user.license_type,
        hashed_password=hashed_password,
        license_active=True
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Create user folder
    user_folder = Path(settings.USER_DATA_PATH) / f"user_{db_user.id}_{db_user.username}"
    user_folder.mkdir(parents=True, exist_ok=True)
    db_user.user_folder = str(user_folder)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@app.get("/api/admin/users", response_model=List[UserResponse])
def admin_get_users(db: Session = Depends(get_db)):
    """Admin get all users"""
    return db.query(User).all()

@app.get("/api/admin/users/{user_id}", response_model=UserResponse)
def admin_get_user(user_id: int, db: Session = Depends(get_db)):
    """Admin get user details"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.put("/api/admin/users/{user_id}", response_model=UserResponse)
def admin_update_user(user_id: int, user_update: UserUpdate, db: Session = Depends(get_db)):
    """Admin update user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    for key, value in user_update.model_dump(exclude_unset=True).items():
        setattr(user, key, value)
    
    db.commit()
    db.refresh(user)
    return user

@app.post("/api/admin/users/{user_id}/toggle-license", response_model=UserResponse)
def admin_toggle_license(user_id: int, license_data: dict, db: Session = Depends(get_db)):
    """Admin toggle user license"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.license_active = license_data.get("license_active", True)
    db.commit()
    db.refresh(user)
    return user

@app.delete("/api/admin/users/{user_id}")
def admin_delete_user(user_id: int, db: Session = Depends(get_db)):
    """Admin delete user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}

# Bookings Management
@app.get("/api/admin/bookings", response_model=List[BookingResponse])
def admin_get_bookings(status: str = None, user_id: int = None, db: Session = Depends(get_db)):
    """Admin get all bookings"""
    query = db.query(Booking)
    if status:
        query = query.filter(Booking.status == status)
    if user_id:
        query = query.filter(Booking.user_id == user_id)
    return query.order_by(Booking.date.desc()).all()

@app.get("/api/admin/bookings/pending", response_model=List[BookingResponse])
def admin_get_pending_bookings(db: Session = Depends(get_db)):
    """Admin get pending bookings"""
    return db.query(Booking).filter(Booking.status == "pending").all()

@app.post("/api/admin/bookings/{booking_id}/confirm", response_model=BookingResponse)
def admin_confirm_booking(booking_id: int, confirm: BookingConfirm, db: Session = Depends(get_db)):
    """Admin confirm/reject booking"""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    booking.status = confirm.status
    booking.admin_response = confirm.admin_response
    booking.confirmed_by = confirm.confirmed_by
    booking.confirmed_at = datetime.now()
    booking.notification_sent = True
    db.commit()
    db.refresh(booking)
    return booking

@app.put("/api/admin/bookings/{booking_id}", response_model=BookingResponse)
def admin_update_booking(booking_id: int, booking_update: BookingUpdate, db: Session = Depends(get_db)):
    """Admin update booking"""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    for key, value in booking_update.model_dump(exclude_unset=True).items():
        setattr(booking, key, value)
    
    db.commit()
    db.refresh(booking)
    return booking

@app.delete("/api/admin/bookings/{booking_id}")
def admin_delete_booking(booking_id: int, db: Session = Depends(get_db)):
    """Admin delete booking"""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    db.delete(booking)
    db.commit()
    return {"message": "Booking deleted successfully"}

# Gallery Management
@app.post("/api/admin/gallery/upload", response_model=GalleryResponse)
async def admin_upload_gallery(
    file: UploadFile = File(...),
    title: str = None,
    description: str = None,
    db: Session = Depends(get_db)
):
    """Admin upload gallery image"""
    file_path = f"static/gallery/{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    db_image = GalleryImage(
        filename=file.filename,
        filepath=file_path,
        title=title,
        description=description
    )
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    return db_image

@app.delete("/api/admin/gallery/{image_id}")
def admin_delete_gallery(image_id: int, db: Session = Depends(get_db)):
    """Admin delete gallery image"""
    image = db.query(GalleryImage).filter(GalleryImage.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    if os.path.exists(image.filepath):
        os.remove(image.filepath)
    
    db.delete(image)
    db.commit()
    return {"message": "Image deleted successfully"}

# Settings Management
@app.put("/api/admin/settings/homepage", response_model=dict)
def admin_update_homepage(update: SettingsUpdate, db: Session = Depends(get_db)):
    """Admin update homepage content"""
    setting = db.query(Settings).filter(Settings.key == "homepage_content").first()
    if not setting:
        setting = Settings(key="homepage_content", value=update.value)
        db.add(setting)
    else:
        setting.value = update.value
    db.commit()
    db.refresh(setting)
    return {"message": "Homepage updated", "value": setting.value}

@app.put("/api/admin/settings/time-slots", response_model=dict)
def admin_update_time_slots(update: SettingsUpdate, db: Session = Depends(get_db)):
    """Admin update time slots"""
    setting = db.query(Settings).filter(Settings.key == "time_slots").first()
    if not setting:
        setting = Settings(key="time_slots", value=update.value)
        db.add(setting)
    else:
        setting.value = update.value
    db.commit()
    db.refresh(setting)
    return {"message": "Time slots updated", "value": setting.value}

# Calendar
@app.get("/api/admin/calendar/today")
def admin_calendar_today(db: Session = Depends(get_db)):
    """Get today's calendar events"""
    today = date.today()
    events = db.query(Booking).filter(
        Booking.date == today,
        Booking.status == "confirmed"
    ).all()
    return events

@app.get("/api/admin/calendar/upcoming")
def admin_calendar_upcoming(days: int = 7, db: Session = Depends(get_db)):
    """Get upcoming calendar events"""
    from datetime import timedelta
    today = date.today()
    future_date = today + timedelta(days=days)
    
    events = db.query(Booking).filter(
        Booking.date >= today,
        Booking.date <= future_date,
        Booking.status == "confirmed"
    ).order_by(Booking.date).all()
    return events

@app.get("/api/admin/calendar/notifications/pending")
def admin_calendar_pending(db: Session = Depends(get_db)):
    """Get pending booking notifications"""
    bookings = db.query(Booking).filter(
        Booking.status == "pending",
        Booking.notification_sent == False
    ).all()
    return {"count": len(bookings), "bookings": bookings}

# Dashboard
@app.get("/api/admin/dashboard/stats")
def admin_dashboard_stats(db: Session = Depends(get_db)):
    """Admin dashboard statistics"""
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.license_active == True).count()
    inactive_users = total_users - active_users
    
    total_bookings = db.query(Booking).count()
    pending_bookings = db.query(Booking).filter(Booking.status == "pending").count()
    confirmed_bookings = db.query(Booking).filter(Booking.status == "confirmed").count()
    completed_bookings = db.query(Booking).filter(Booking.status == "completed").count()
    
    total_documents = db.query(UserDocument).count()
    
    return {
        "users": {
            "total": total_users,
            "active": active_users,
            "inactive": inactive_users
        },
        "bookings": {
            "total": total_bookings,
            "pending": pending_bookings,
            "confirmed": confirmed_bookings,
            "completed": completed_bookings
        },
        "documents": {
            "total": total_documents
        }
    }

@app.get("/api/admin/dashboard/recent-activity")
def admin_recent_activity(limit: int = 10, db: Session = Depends(get_db)):
    """Get recent activity"""
    recent_bookings = db.query(Booking).order_by(Booking.created_at.desc()).limit(limit).all()
    recent_users = db.query(User).order_by(User.created_at.desc()).limit(limit).all()
    
    return {
        "recent_bookings": recent_bookings,
        "recent_users": recent_users
    }

# Documents
@app.get("/api/admin/documents/user/{user_id}", response_model=List[DocumentOut])
def list_user_documents(user_id: int, db: Session = Depends(get_db)):
    docs = db.query(UserDocument).filter(UserDocument.user_id == user_id).all()
    result = []
    for d in docs:
        download_url = f"/api/admin/documents/download/{d.id}"
        # Convert to dict first, then add download_url
        doc_dict = {
            "id": d.id,
            "user_id": d.user_id,
            "filename": d.filename,
            "category": d.category,
            "description": d.description,
            "uploaded_at": d.uploaded_at,
            "download_url": download_url
        }
        result.append(DocumentOut(**doc_dict))
    return result

# Also fix the admin_upload_document endpoint
@app.post("/api/admin/documents/upload/{user_id}", response_model=DocumentOut)
async def admin_upload_document(
    user_id: int,
    file: UploadFile = File(...),
    category: str = None,
    description: str = None,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    file_bytes = await file.read()

    document = UserDocument(
        user_id=user_id,
        filename=file.filename,
        original_filename=file.filename,
        file_type=file.content_type,
        file_size=len(file_bytes),
        file_path=None,
        file_data=file_bytes,
        category=category,
        description=description
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    download_url = f"/api/admin/documents/download/{document.id}"
    return DocumentOut(
        id=document.id,
        user_id=document.user_id,
        filename=document.filename,
        category=document.category,
        description=document.description,
        uploaded_at=document.uploaded_at,
        download_url=download_url
    )
# Add this endpoint to serve images directly (for frontend display)
@app.get("/api/admin/documents/view/{doc_id}")
def view_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(UserDocument).filter(UserDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(404, "Document not found")
    
    return StreamingResponse(
        BytesIO(doc.file_data),
        media_type=doc.file_type or "application/octet-stream",
        headers={"Content-Disposition": f"inline; filename={doc.filename}"}
    )


# ==================== user profile ====================


# Add these imports at the top (if not already present)
from datetime import timedelta
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

# Add these configurations after pwd_context
SECRET_KEY = "your-secret-key-change-this-in-production"  # Change this!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/customer/login")

# Add these new schemas after existing schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class TokenData(BaseModel):
    email: Optional[str] = None

class CustomerLogin(BaseModel):
    email: EmailStr
    password: str

class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[str] = None
    nationality: Optional[str] = None
    experience_years: Optional[int] = None
    previous_roles: Optional[str] = None
    skills: Optional[str] = None
    preferred_country: Optional[str] = None
    preferred_city: Optional[str] = None

class PasswordUpdate(BaseModel):
    old_password: str
    new_password: str

# Add helper functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.email == token_data.email).first()
    if user is None:
        raise credentials_exception
    
    # Check if user is active
    if not user.license_active:
        raise HTTPException(status_code=403, detail="Your account is not active. Please contact administrator.")
    
    return user

# ==================== NEW CUSTOMER AUTH & PROFILE ROUTES ====================

@app.post("/api/customer/login", response_model=Token)
async def customer_login(form_data: CustomerLogin, db: Session = Depends(get_db)):
    """Customer login endpoint"""
    user = db.query(User).filter(User.email == form_data.email).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    if not user.hashed_password:
        raise HTTPException(
            status_code=401, 
            detail="No password set. Please contact administrator to set up your password."
        )
    
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    # Check if account is active
    if not user.license_active:
        raise HTTPException(
            status_code=403, 
            detail="Your account is not active. Please contact administrator."
        )
    
    # Update last login
    user.last_login = datetime.now()
    db.commit()
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@app.get("/api/customer/profile/me", response_model=UserResponse)
async def get_customer_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return current_user

@app.put("/api/customer/profile/me", response_model=UserResponse)
async def update_customer_profile(
    profile_update: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update customer profile"""
    for key, value in profile_update.model_dump(exclude_unset=True).items():
        setattr(current_user, key, value)
    
    current_user.updated_at = datetime.now()
    db.commit()
    db.refresh(current_user)
    return current_user

@app.post("/api/customer/profile/change-password")
async def change_customer_password(
    password_update: PasswordUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change customer password"""
    if not current_user.hashed_password:
        raise HTTPException(status_code=400, detail="No password set. Contact administrator.")
    
    if not verify_password(password_update.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect current password")
    
    current_user.hashed_password = get_password_hash(password_update.new_password)
    db.commit()
    
    return {"message": "Password changed successfully"}

@app.get("/api/customer/profile/documents", response_model=List[DocumentOut])
async def get_customer_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all documents for current user"""
    docs = db.query(UserDocument).filter(UserDocument.user_id == current_user.id).all()
    result = []
    for d in docs:
        download_url = f"/api/customer/profile/documents/download/{d.id}"
        doc_dict = {
            "id": d.id,
            "user_id": d.user_id,
            "filename": d.filename,
            "category": d.category,
            "description": d.description,
            "uploaded_at": d.uploaded_at,
            "download_url": download_url
        }
        result.append(DocumentOut(**doc_dict))
    return result

@app.post("/api/customer/profile/documents/upload", response_model=DocumentOut)
async def upload_customer_document(
    file: UploadFile = File(...),
    category: str = None,
    description: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload document for current user"""
    file_bytes = await file.read()

    document = UserDocument(
        user_id=current_user.id,
        filename=file.filename,
        original_filename=file.filename,
        file_type=file.content_type,
        file_size=len(file_bytes),
        file_path=None,
        file_data=file_bytes,
        category=category,
        description=description
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    download_url = f"/api/customer/profile/documents/download/{document.id}"
    return DocumentOut(
        id=document.id,
        user_id=document.user_id,
        filename=document.filename,
        category=document.category,
        description=document.description,
        uploaded_at=document.uploaded_at,
        download_url=download_url
    )

@app.get("/api/customer/profile/documents/download/{doc_id}")
async def download_customer_document(
    doc_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download document (only own documents)"""
    doc = db.query(UserDocument).filter(
        UserDocument.id == doc_id,
        UserDocument.user_id == current_user.id
    ).first()
    
    if not doc:
        raise HTTPException(404, "Document not found")
    
    return StreamingResponse(
        BytesIO(doc.file_data),
        media_type=doc.file_type or "application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={doc.filename}"}
    )

@app.delete("/api/customer/profile/documents/{doc_id}")
async def delete_customer_document(
    doc_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete own document"""
    doc = db.query(UserDocument).filter(
        UserDocument.id == doc_id,
        UserDocument.user_id == current_user.id
    ).first()
    
    if not doc:
        raise HTTPException(404, "Document not found")
    
    db.delete(doc)
    db.commit()
    return {"message": "Document deleted successfully"}

@app.get("/api/customer/profile/bookings", response_model=List[BookingResponse])
async def get_customer_bookings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all bookings for current user"""
    bookings = db.query(Booking).filter(Booking.email == current_user.email).order_by(Booking.date.desc()).all()
    return bookings

@app.get("/api/customer/profile/bookings/status/{status}", response_model=List[BookingResponse])
async def get_customer_bookings_by_status(
    status: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get bookings by status (pending, confirmed, rejected)"""
    bookings = db.query(Booking).filter(
        Booking.email == current_user.email,
        Booking.status == status
    ).order_by(Booking.date.desc()).all()
    return bookings

# ==================== ADMIN: Set User Password (New) ====================

class SetPasswordRequest(BaseModel):
    password: str

@app.post("/api/admin/users/{user_id}/set-password")
def admin_set_user_password(
    user_id: int,
    password_req: SetPasswordRequest,
    db: Session = Depends(get_db)
):
    """Admin sets password for a user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.hashed_password = get_password_hash(password_req.password)
    db.commit()
    
    return {
        "message": "Password set successfully",
        "user_id": user_id,
        "email": user.email
    }

# ==================== ====================

@app.get("/")
def root():
    return {
        "message": "Unified Employee Agency API v3.0",
        "description": "Combined Customer Website + Admin Portal",
        "features": [
            "Customer Registration & Booking",
            "Admin User Management",
            "License Control System",
            "Calendar & Notifications",
            "Document Management",
            "Gallery Management",
            "Dashboard Analytics"
        ],
        "endpoints": {
            "customer": "/api/customer/*",
            "admin": "/api/admin/*",
            "docs": "/docs"
        }
    }

@app.get("/health")
def health():
    return {"status": "healthy", "version": "3.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
