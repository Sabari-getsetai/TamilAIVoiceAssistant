#!/usr/bin/env python3
"""
Quick verification script to test if the setup is correct
"""
import sys
from pathlib import Path

print("🔍 Verifying Tamil AI Voice Assistant Setup...\n")

# Check Python version
print(f"✓ Python version: {sys.version.split()[0]}")

# Check if virtual environment exists
venv_path = Path(".venv")
if venv_path.exists():
    print("✓ Virtual environment found")
else:
    print("✗ Virtual environment not found - run: python3 -m venv .venv")
    sys.exit(1)

# Try importing key dependencies
print("\nChecking dependencies:")

try:
    import fastapi
    print(f"✓ FastAPI {fastapi.__version__}")
except ImportError:
    print("✗ FastAPI not installed - run: pip install -r requirements.txt")
    sys.exit(1)

try:
    import uvicorn
    print(f"✓ Uvicorn installed")
except ImportError:
    print("✗ Uvicorn not installed")
    sys.exit(1)

try:
    import pydantic_settings
    print(f"✓ Pydantic Settings installed")
except ImportError:
    print("✗ Pydantic Settings not installed")
    sys.exit(1)

# Check directory structure
print("\nChecking directory structure:")
required_dirs = [
    "backend",
    "backend/api",
    "backend/graphs",
    "backend/rag",
    "backend/speech",
    "backend/models",
    "app/web",
    "data",
    "models"
]

for dir_path in required_dirs:
    if Path(dir_path).exists():
        print(f"✓ {dir_path}/")
    else:
        print(f"✗ {dir_path}/ not found")

# Check key files
print("\nChecking key files:")
required_files = [
    "requirements.txt",
    "backend/main.py",
    "backend/settings.py",
    "app/web/package.json",
    ".gitignore",
    ".vscode/launch.json"
]

for file_path in required_files:
    if Path(file_path).exists():
        print(f"✓ {file_path}")
    else:
        print(f"✗ {file_path} not found")

# Test importing backend modules
print("\nTesting backend imports:")
try:
    sys.path.insert(0, str(Path.cwd()))
    from backend.settings import settings
    print(f"✓ Settings module loaded")
    print(f"  - API Host: {settings.API_HOST}")
    print(f"  - API Port: {settings.API_PORT}")
    print(f"  - Data Root: {settings.DATA_ROOT}")
except Exception as e:
    print(f"✗ Failed to import settings: {e}")
    sys.exit(1)

try:
    from backend.main import app
    print(f"✓ FastAPI app loaded")
except Exception as e:
    print(f"✗ Failed to import app: {e}")
    sys.exit(1)

print("\n" + "="*50)
print("✅ Setup verification complete!")
print("="*50)
print("\nYou can now:")
print("1. Run backend: python -m uvicorn backend.main:app --reload")
print("2. Run frontend: cd app/web && npm run dev")
print("3. Or use VSCode launch configurations (F5)")
