# 🎯 UNIFIED BACKEND - Employee Agency System

## Overview

**Single FastAPI backend** serving both:
- ✅ **Customer Website** (Registration, Booking, Gallery)
- ✅ **Admin Portal** (User Management, License Control, Calendar, Dashboard)

**One Backend, Two Frontends, One Database**

---

## 🚀 Quick Start

```bash
# Install dependencies
conda activate sura

pip install -r requirements.txt

# Run server
python main.py
```

**Backend runs on:** http://localhost:8000  
**API Docs:** http://localhost:8000/docs

---

## 📋 Database Setup

Uses existing database credentials:
```
Host: localhost
Port: 5432
Database: gen
User: postgres
Password: 123456789
```

Tables are created automatically on first run.

---

## 🎯 API Structure

### Customer API (`/api/customer/`)
- `POST /api/customer/register/start` - Start registration
- `PUT /api/customer/register/update/{id}` - Update registration
- `POST /api/customer/register/upload-cv/{id}` - Upload CV
- `POST /api/customer/booking/create` - Create booking
- `GET /api/customer/gallery` - Get gallery images
- `GET /api/customer/settings/homepage` - Get homepage content
- `GET /api/customer/settings/time-slots` - Get time slots

### Admin API (`/api/admin/`)

**Users:**
- `POST /api/admin/users` - Create user
- `GET /api/admin/users` - List all users
- `GET /api/admin/users/{id}` - Get user details
- `PUT /api/admin/users/{id}` - Update user
- `POST /api/admin/users/{id}/toggle-license` - Toggle license
- `DELETE /api/admin/users/{id}` - Delete user

**Bookings:**
- `GET /api/admin/bookings` - List bookings (filter by status/user)
- `GET /api/admin/bookings/pending` - Get pending bookings
- `POST /api/admin/bookings/{id}/confirm` - Confirm/reject booking
- `PUT /api/admin/bookings/{id}` - Update booking
- `DELETE /api/admin/bookings/{id}` - Delete booking

**Gallery:**
- `POST /api/admin/gallery/upload` - Upload image
- `DELETE /api/admin/gallery/{id}` - Delete image

**Calendar:**
- `GET /api/admin/calendar/today` - Today's events
- `GET /api/admin/calendar/upcoming?days=7` - Upcoming events
- `GET /api/admin/calendar/notifications/pending` - Pending notifications

**Dashboard:**
- `GET /api/admin/dashboard/stats` - Statistics
- `GET /api/admin/dashboard/recent-activity` - Recent activity

**Documents:**
- `POST /api/admin/documents/upload/{user_id}` - Upload document
- `GET /api/admin/documents/user/{user_id}` - Get user documents
- `GET /api/admin/documents/{id}/download` - Download document

**Settings:**
- `PUT /api/admin/settings/homepage` - Update homepage
- `PUT /api/admin/settings/time-slots` - Update time slots

---

## 📊 Database Tables

### users
- Customer registrations + Admin-created users
- License management (`license_active`, `license_type`)
- Registration progress (`current_step`, `registration_status`)
- User folders for document storage

### bookings
- Customer bookings + Admin bookings
- Calendar integration
- Notification tracking
- Admin confirmation workflow

### gallery_images
- Shared gallery for customer website
- Admin-managed

### user_documents
- File storage (filesystem + optional BLOB)
- Per-user document management

### calendar_events
- Auto-created from bookings
- Admin notifications

### settings
- Homepage content
- Time slots
- System configuration

---

## 🔥 Key Features

### 1. Unified User Model
- Supports both customer registration AND admin-created users
- Single user table with all fields
- License control for access management

### 2. Flexible Booking System
- Customers can book without user account
- Or link booking to registered user
- Admin confirmation workflow
- Auto calendar integration

### 3. Document Management
- User-specific folders: `user_data/user_{id}_{username}/`
- Optional database BLOB storage
- Admin can upload for any user

### 4. Gallery Management
- Shared across customer site
- Admin controls uploads/deletes

### 5. Settings System
- Dynamic homepage content
- Configurable time slots
- JSON storage for flexibility

---

## 🎨 Frontend Integration

### Customer Frontend

Update API base URL in customer frontend:
```javascript
const API_BASE = 'http://localhost:8000/api/customer';
```

Customer endpoints don't require authentication.

### Admin Frontend

Update API base URL in admin frontend:
```javascript
const API_BASE = 'http://localhost:8000/api/admin';
```

Admin endpoints assume PIN-protected frontend (no backend auth needed for simplicity).

---

## 📁 Project Structure

```
unified-backend/
├── main.py                 # Complete FastAPI app with all routes
├── config.py               # Configuration
├── database.py             # Database setup
├── requirements.txt        # Dependencies
├── .env                   # Environment variables
│
├── models/                # SQLAlchemy models
│   ├── __init__.py
│   ├── user.py           # Unified user model
│   ├── booking.py        # Booking model
│   ├── gallery.py        # Gallery model
│   ├── document.py       # Document model
│   ├── calendar_event.py # Calendar model
│   └── settings.py       # Settings model
│
├── static/               # Static files
│   ├── cv/              # Customer CV uploads
│   └── gallery/         # Gallery images
│
└── user_data/           # User document folders
    └── user_{id}_{username}/
```

---

## 🔧 Configuration

### Environment Variables (`.env`)
```
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=gen
POSTGRES_USER=postgres
POSTGRES_PASSWORD=123456789
DATABASE_URL=postgresql://postgres:123456789@localhost:5432/gen
SECRET_KEY=your-secret-key
USER_DATA_PATH=./user_data
```

---

## 🚦 Usage Examples

### Customer Registration Flow

```bash
# 1. Start registration
POST /api/customer/register/start
Body: {
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890"
}
Response: { "id": 1, "email": "john@example.com", ... }

# 2. Update with experience
PUT /api/customer/register/update/1
Body: {
  "experience_years": 5,
  "skills": "Python, React",
  "preferred_country": "Germany",
  "current_step": 3
}

# 3. Upload CV
POST /api/customer/register/upload-cv/1
FormData: file=cv.pdf
```

### Customer Booking

```bash
POST /api/customer/booking/create
Body: {
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+1234567890",
  "purpose": "Job interview",
  "date": "2024-12-15",
  "time": "14:00"
}
```

### Admin License Toggle

```bash
POST /api/admin/users/1/toggle-license
Body: {
  "license_active": false
}
```

### Admin Confirm Booking

```bash
POST /api/admin/bookings/5/confirm
Body: {
  "status": "confirmed",
  "admin_response": "Your interview is scheduled",
  "confirmed_by": "Admin"
}
```

---

## ✅ Migration from Two Backends

If you have data in separate backends:

1. **Users**: Existing customer registrations remain
2. **Bookings**: Existing bookings remain
3. **Update API URLs** in both frontends to point to unified backend
4. **Test each endpoint** to ensure compatibility

---

## 🎯 Benefits of Unified Backend

1. ✅ **Single Database** - No data duplication
2. ✅ **Shared Models** - Consistent data structure
3. ✅ **Easy Deployment** - One backend to maintain
4. ✅ **Better Integration** - Customer & admin data in sync
5. ✅ **Simplified Setup** - One installation, one configuration
6. ✅ **Cost Effective** - Single server deployment

---

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Kill process on port 8000
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

### Database Connection Error
- Verify PostgreSQL is running
- Check credentials in `.env`
- Ensure database `gen` exists

### Import Errors
```bash
pip install -r requirements.txt --upgrade
```

---

## 📖 API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Interactive documentation with try-it-out feature.

---

## 🎉 You're Ready!

1. Install: `pip install -r requirements.txt`
2. Run: `python main.py`
3. Test: http://localhost:8000
4. Docs: http://localhost:8000/docs

**One backend, serving both customer and admin frontends!**
