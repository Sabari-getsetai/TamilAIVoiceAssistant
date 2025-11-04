# VS Code Configuration for Next.js Development

This document explains the updated VS Code configuration for running the Tamil AI Voice Assistant with the new Next.js frontend.

## Updated Configuration Files

### 1. `.vscode/launch.json`

The launch configuration now includes:

#### Debug Configurations:
- **Backend: FastAPI** - Runs the Python FastAPI backend with debugging
- **Frontend: Next.js** - Runs the Next.js development server
- **Frontend: Vite React (Legacy)** - Keeps the old Vite configuration for reference

#### Compound Configurations:
- **Full Stack: Backend + Next.js** - Primary configuration that starts both backend and Next.js frontend
- **Full Stack: Backend + Vite (Legacy)** - Legacy configuration for the old Vite setup

### 2. `.vscode/tasks.json`

The tasks configuration now includes:

#### Installation Tasks:
- **Install Python Dependencies** - Installs backend Python packages
- **Install Next.js Dependencies** - Installs Next.js npm packages
- **Install Vite Dependencies (Legacy)** - Legacy Vite package installation

#### Development Tasks:
- **Run Backend (Terminal)** - Starts FastAPI backend in terminal
- **Run Next.js (Terminal)** - Starts Next.js dev server in terminal
- **Run Vite (Terminal - Legacy)** - Legacy Vite dev server

#### Production Tasks:
- **Build Next.js** - Builds Next.js for production
- **Start Next.js Production** - Starts Next.js in production mode

## How to Use

### Method 1: Using F5 Debug (Recommended)
1. Press `F5` or go to Run and Debug panel
2. Select "Full Stack: Backend + Next.js" from the dropdown
3. Click the play button or press `F5`
4. Both backend and frontend will start automatically
5. Browser will open automatically when Next.js is ready

### Method 2: Using Tasks
1. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
2. Type "Tasks: Run Task"
3. Select the desired task:
   - "Run Backend (Terminal)" for just the backend
   - "Run Next.js (Terminal)" for just the frontend

### Method 3: Using Terminal Commands
```bash
# Backend (from project root)
source .venv/bin/activate
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (from project root)
cd app/nextjs
npm run dev
```

## Application URLs

- **Next.js Frontend**: http://localhost:3000
- **FastAPI Backend**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Key Features

### Auto Browser Opening
The Next.js configuration includes `serverReadyAction` that automatically opens your browser when the development server is ready.

### Dedicated Terminals
Each service runs in its own dedicated terminal panel for easy monitoring and debugging.

### Legacy Support
The old Vite configuration is preserved as "Legacy" options, so you can still run the old frontend if needed.

### Production Ready
Includes tasks for building and running Next.js in production mode.

## Troubleshooting

### Port Conflicts
- Backend runs on port 8000
- Next.js runs on port 3000
- If ports are in use, stop other services or change ports in the configuration

### Dependencies
Make sure to install dependencies:
```bash
# Python dependencies
pip install -r requirements.txt

# Next.js dependencies
cd app/nextjs && npm install
```

### Environment Variables
Ensure `.env.local` file exists in `app/nextjs/` with:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Migration Notes

- The primary frontend is now Next.js instead of Vite
- All new development should use the Next.js configuration
- The Vite configuration is kept for backward compatibility
- The compound configuration "Full Stack: Backend + Next.js" is now the default

## Benefits of Next.js Configuration

1. **Better Performance**: Server-side rendering and optimized builds
2. **Improved SEO**: Better search engine optimization
3. **Enhanced Developer Experience**: Built-in TypeScript support and hot reloading
4. **Professional UI**: Material-UI components with consistent design
5. **Scalability**: Modular architecture for future enhancements
