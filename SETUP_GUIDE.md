# 🚀 VeriLens - Setup & Usage Guide

## ✅ Application Status

Your **VeriLens Digital Asset Protection System** is now **fully working and ready to use**!

### Server Status
- ✅ **Backend API**: Running on http://127.0.0.1:8000
  - API Documentation: http://127.0.0.1:8000/docs  
  - ReDoc: http://127.0.0.1:8000/redoc
  
- ✅ **Frontend**: Running on http://127.0.0.1:5174
  - Dashboard: http://127.0.0.1:5174

---

## 🔐 Demo Account Credentials

```
Email:    admin@demo.org
Password: demo123
```

---

## 🎯 Quick Start

### Option 1: Run Everything with One Command

```bash
# From the root directory
python wsgi.py             # Terminal 1: Starts Backend
# In another terminal:
cd frontend && npm run dev # Terminal 2: Starts Frontend
```

### Option 2: Run Services Individually

**Backend:**
```bash
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

**Frontend:**
```bash
cd frontend
npm run dev
```

---

## 📂 Project Structure

```
asset_protection/
├── backend/                 # FastAPI server
│   ├── app/
│   │   ├── main.py         # Application entry point
│   │   ├── routers/        # API endpoints
│   │   ├── models/         # Database models
│   │   ├── services/       # Business logic
│   │   └── config.py       # Configuration
│   ├── requirements.txt     # Python dependencies
│   ├── .env               # Environment variables
│   └── verilens.db        # SQLite database
│
├── frontend/               # React + Vite
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── pages/         # Page components
│   │   ├── lib/           # API client
│   │   └── hooks/         # React hooks
│   ├── package.json       # NPM dependencies
│   └── .env              # Frontend config
│
└── ai_engine/            # AI fingerprinting pipeline

```

---

## 🗄️ Database

**Location**: `backend/data/verilens.db` (SQLite)

**Tables Created**:
- `organisations` - Company/team data
- `users` - User accounts 
- `assets` - Protected media files
- `violations` - Infringement reports
- `enforcement_records` - DMCA & takedown actions

**Seeded Demo Data**:
- 1 Organization (Demo Organisation)
- 1 User (admin@demo.org)
- 1 Test Asset
- 1 Test Violation Record

---

## ✨ Features Ready to Use

### Dashboard
- Real-time stats (assets, violations, takedowns)
- Propagation graph visualization
- Morph score monitoring
- Live alerts panel

### Asset Management
- Upload protected media
- Auto-fingerprinting
- Search similar assets
- Track all matches

### Violation Management
- View detected infringements
- Check morph scores & confidence
- File DMCA takedowns
- Track enforcement actions

### High-Risk Accounts
- Monitor repeat offenders
- View risk distribution
- Track across platforms
- Enforce against accounts

### Real-Time Alerts
- WebSocket-based notifications
- Severity filtering
- Mark as read tracking
- External link navigation

---

## 🔗 API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/token` - Login
- `GET /auth/me` - Get current user

### Assets
- `GET /assets` - List all assets
- `POST /assets` - Upload asset
- `GET /assets/{id}` - Get asset details

### Search
- `POST /search` - Search similar assets

### Violations
- `GET /violations` - List violations
- `GET /violations/{id}` - Get violation details
- `PATCH /violations/{id}` - Update violation status
- `POST /violations/{id}/enforcement` - Create enforcement record

### Other
- `GET /stats/dashboard` - Dashboard stats
- `GET /propagation/{asset_id}` - Propagation graph
- `WebSocket /ws/alerts` - Real-time alerts

---

## 🎨 Frontend Features

### Pages Implemented
✅ Dashboard - Main overview
✅ Protected Assets - Asset management
✅ High-Risk Accounts - Risk tracking
✅ Enforcement Actions - Action history
✅ Alerts - Real-time notifications
✅ Propagation Graph - Content spread
✅ System Health - Service status
✅ Upload - Media fingerprinting

### UI Components
✅ Header with global search
✅ Sidebar navigation
✅ Real-time alerts panel
✅ Sortable data tables
✅ Interactive graphs (D3.js)
✅ Status indicators
✅ Action modals
✅ Upload dropzone

---

## 🛠️ Development Workflow

### Backend Development
```bash
cd backend

# Run tests
pytest

# Create new migration
alembic upgrade head

# Generate migrations
alembic revision --autogenerate -m "Description"
```

### Frontend Development
```bash
cd frontend

# Run linter
npm run lint

# Build for production
npm run build

# Preview production build
npm run preview
```

---

## 🐛 Troubleshooting

### Backend Won't Start

**Issue**: `ModuleNotFoundError: No module named 'app'`  
**Solution**: Use the `wsgi.py` wrapper or ensure you're in the `backend/` directory

**Issue**: Database locked
**Solution**: Delete `backend/data/verilens.db` and `backend/verilens.db`, then restart

**Issue**: Port 8000 already in use
**Solution**: Change port in wsgi.py or kill the process using `lsof -ti:8000 | xargs kill -9`

### Frontend Won't Start

**Issue**: Port 5173 occupied
**Solution**: Vite will auto-use 5174, or kill existing process

**Issue**: Dependencies missing
**Solution**: Run `npm install` in frontend directory

### API Connection Failed

**Issue**: Frontend can't reach backend
**Solution**: Check `frontend/.env` has `VITE_API_BASE_URL=http://localhost:8000`

---

## 📊 Data Locations

**Application Data**:
- Database: `backend/data/verilens.db`
- Uploads: `backend/uploads/`
- Logs: Console output
- Vector index: In-memory (Milvus adapter)
- Graph data: In-memory (Neo4j adapter)

**Configuration**:
- Backend: `backend/.env`
- Frontend: `frontend/.env`

---

## 🔄 Integration Points

### Frontend → Backend Communication
✅ JWT authentication via Bearer tokens
✅ REST API for CRUD operations
✅ WebSocket for real-time alerts
✅ File uploads via FormData
✅ Error handling with toast notifications
✅ Loading states and spinners

### Backend → AI Engine
- Fingerprint extraction from media
- Vector similarity computation
- Propagation chain analysis

### Backend → Services
- SQLAlchemy for database ORM
- Milvus adapter for vector search
- Neo4j adapter for graph data
- Celery for async tasks

---

## 📱 Technology Stack

**Backend**:
- FastAPI - REST API framework
- SQLAlchemy - ORM
- Pydantic - Data validation
- PyJWT - Authentication
- SQLite - Database

**Frontend**:
- React 19 - UI framework
- Vite - Build tool
- Recharts - Charts & graphs
- D3.js - Data visualization
- Framer Motion - Animations
- Lucide React - Icons

**Infrastructure**:
- Python 3.14+
- Node.js 18+
- SQLite (no external DB needed)

---

## ✅ Verification Checklist

- [x] Backend server running on :8000
- [x] Frontend server running on :5173/:5174
- [x] Database initialized with demo data
- [x] API documentation accessible
- [x] Frontend-backend integration complete
- [x] All buttons wired to API endpoints
- [x] Real-time WebSocket alerts working
- [x] Authentication system functional
- [x] File uploads operational  
- [x] Demo data seeded

---

## 📝 Next Steps

1. **Login** with `admin@demo.org / demo123`
2. **Upload** a test asset
3. **Search** for similar content
4. **File** a DMCA takedown
5. **View** enforcement records
6. **Monitor** real-time alerts

---

## 🆘 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review API docs at http://127.0.0.1:8000/docs
3. Check browser console for frontend errors
4. Review terminal output for backend errors
5. Verify `.env` files are configured correctly

---

**Status**: ✅ **FULLY OPERATIONAL**  
**Last Updated**: April 18, 2026  
**Version**: 1.0.0
