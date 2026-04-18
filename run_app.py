#!/usr/bin/env python
"""Setup and run the complete VeriLens application"""

import subprocess
import time
import sys
import os

def run_backend():
    """Start backend server"""
    print("\n" + "="*60)
    print("🚀 STARTING VERILENS BACKEND SERVER")
    print("="*60)
    backend_dir = os.path.join(os.path.dirname(__file__), "backend")
    cmd = [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"]
    
    try:
        subprocess.Popen(cmd, cwd=backend_dir)
        print("✓ Backend started on http://127.0.0.1:8000")
        print("✓ API Docs available at http://127.0.0.1:8000/docs")
    except Exception as e:
        print(f"✗ Failed to start backend: {e}")
        return False
    
    return True

def run_frontend():
    """Start frontend dev server"""
    print("\n" + "="*60)
    print("🎨 STARTING VERILENS FRONTEND SERVER")
    print("="*60)
    frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
    cmd = ["npm", "run", "dev"]
    
    try:
        subprocess.Popen(cmd, cwd=frontend_dir, shell=True)
        print("✓ Frontend starting on http://127.0.0.1:5173")
    except Exception as e:
        print(f"✗ Failed to start frontend: {e}")
        return False
    
    return True

def main():
    """Main entry point"""
    print("\n" + "█"*60)
    print("█" + " "*58 + "█")
    print("█" + "  VERILENS - Digital Asset Protection System".center(58) + "█")
    print("█" + " "*58 + "█")
    print("█"*60)
    
    # Start backend
    if not run_backend():
        sys.exit(1)
    
    time.sleep(2)
    
    # Start frontend
    if not run_frontend():
        sys.exit(1)
    
    print("\n" + "="*60)
    print("✅ APPLICATION READY")
    print("="*60)
    print("\n📱 Frontend:  http://127.0.0.1:5173")
    print("🔧 Backend:   http://127.0.0.1:8000")
    print("📚 API Docs:  http://127.0.0.1:8000/docs")
    print("\n👤 Demo Credentials:")
    print("   Email: admin@demo.org")
    print("   Password: demo123")
    print("\n" + "="*60)
    print("Press Ctrl+C to stop all servers\n")
    
    # Keep the script running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down...")
        sys.exit(0)

if __name__ == "__main__":
    main()
