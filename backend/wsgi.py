"""Entry point to run the UVicorn server from the backend"""
import sys
import os

# Add backend to Python path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

if __name__ == "__main__":
    from app.main import app
    from uvicorn import run
    
    run(app, host="127.0.0.1", port=8000, log_level="info")
