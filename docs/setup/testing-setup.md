# Setup Testing Guide

## Prerequisites

Before testing, ensure you have:
- Python 3.10+ installed
- Node.js 18+ and npm installed
- VSCode installed (for using launch configurations)

## Option 1: Using VSCode Launch Configurations (Recommended)

### Install Python Extension for VSCode
1. Install the **Python** extension by Microsoft
2. Install the **Debugpy** extension (it should install automatically with Python extension)

### Running the Application

1. **Run Backend Only**
   - Press `F5` or go to Run and Debug (Ctrl+Shift+D)
   - Select `Backend: FastAPI` from the dropdown
   - Click the green play button
   - Backend will start at `http://localhost:8000`
   - Test health endpoint: `http://localhost:8000/health`

2. **Run Frontend Only**
   - Press `F5` or go to Run and Debug
   - Select `Frontend: Vite React` from the dropdown
   - Click the green play button
   - Frontend will start at `http://localhost:5173`
   - Browser should open automatically

3. **Run Both Together**
   - Select `Full Stack: Backend + Frontend` from the dropdown
   - Click the green play button
   - Both services will start simultaneously

## Option 2: Using VSCode Tasks

1. Open Command Palette (`Ctrl+Shift+P` or `Cmd+Shift+P`)
2. Type "Tasks: Run Task"
3. Select one of:
   - `Install Python Dependencies` - Install backend dependencies
   - `Install Frontend Dependencies` - Install frontend dependencies
   - `Run Backend (Terminal)` - Start FastAPI server
   - `Run Frontend (Terminal)` - Start Vite dev server

## Option 3: Manual Command Line

### Backend Setup & Run
```bash
# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
# OR
.venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run backend
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup & Run
```bash
# Navigate to frontend
cd app/web

# Install dependencies
npm install

# Run frontend
npm run dev
```

## Testing Endpoints

Once the backend is running, you can test these endpoints:

### Root Endpoint
```bash
curl http://localhost:8000/
```

Expected response:
```json
{
  "name": "Tamil AI Voice Assistant",
  "version": "0.1.0",
  "status": "running"
}
```

### Health Check
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-30T...",
  "services": {
    "api": "running",
    "models": "not loaded",
    "vector_store": "not initialized"
  }
}
```

### Frontend
Open browser and navigate to: `http://localhost:5173`

You should see the default Vite React page with the React logo.

## Troubleshooting

### Backend Issues

**Error: "No module named 'fastapi'"**
- Make sure virtual environment is activated
- Run: `pip install -r requirements.txt`

**Error: "Address already in use"**
- Port 8000 is already in use
- Change port in `backend/settings.py` or stop other service using port 8000

**Error: "ModuleNotFoundError: No module named 'backend'"**
- Make sure you're running from the project root directory
- Set PYTHONPATH: `export PYTHONPATH="${PYTHONPATH}:$(pwd)"`

### Frontend Issues

**Error: "Cannot find module"**
- Run: `npm install` in `app/web` directory

**Error: "Port 5173 already in use"**
- Stop other Vite dev server or change port in `vite.config.ts`

## Next Steps

After confirming both services run successfully:
1. Verify CORS by making a request from frontend to backend
2. Check browser console for any errors
3. Proceed to Phase 2: Model Download & Setup
