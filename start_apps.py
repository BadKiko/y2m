#!/usr/bin/env python3
"""
Quick start script for MQTT2Yandex Bridge
"""
import os
import sys
import subprocess
import time
from pathlib import Path

def set_environment():
    """Set development environment variables"""
    os.environ.setdefault('APP_ENV', 'development')
    os.environ.setdefault('SECRET_KEY', 'dev-secret-key-for-testing-purposes-only')
    os.environ.setdefault('ENCRYPTION_KEY', 'dev-encryption-key-for-testing-purposes-only')
    os.environ.setdefault('DATABASE_URL', 'sqlite+aiosqlite:///./dev.db')
    os.environ.setdefault('MQTT_BROKER', 'localhost')
    os.environ.setdefault('MQTT_PORT', '1883')
    os.environ.setdefault('ADMIN_USER', 'admin')
    os.environ.setdefault('ADMIN_PASS', 'admin123')
    os.environ.setdefault('YAPI_URL', 'http://localhost:8080')

def start_fastapi():
    """Start FastAPI application"""
    print("🚀 Starting FastAPI backend...")
    cmd = [
        sys.executable, "-m", "uvicorn",
        "app.main:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload"
    ]
    return subprocess.Popen(cmd, cwd=os.path.dirname(__file__))

def start_streamlit():
    """Start Streamlit application"""
    print("🎨 Starting Streamlit UI...")
    cmd = [
        sys.executable, "-m", "streamlit", "run",
        "streamlit_app/app.py",
        "--server.port", "8501",
        "--server.address", "0.0.0.0"
    ]
    return subprocess.Popen(cmd, cwd=os.path.dirname(__file__))

def check_apps():
    """Check if applications are running"""
    import urllib.request

    apps = [
        ("FastAPI Backend", "http://localhost:8000/health"),
        ("Streamlit UI", "http://localhost:8501/healthz")
    ]

    for name, url in apps:
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                print(f"✅ {name}: Running")
        except Exception as e:
            print(f"❌ {name}: Not responding ({e})")

def main():
    print("🎉 MQTT2Yandex Bridge - Quick Start")
    print("=" * 50)

    # Set environment
    set_environment()

    # Start applications
    fastapi_process = start_fastapi()
    time.sleep(3)  # Wait for FastAPI to start

    streamlit_process = start_streamlit()
    time.sleep(5)  # Wait for Streamlit to start

    # Check status
    print("\n📊 Checking application status...")
    check_apps()

    print("\n🎯 Access Information:")
    print("  • FastAPI Backend: http://localhost:8000")
    print("  • API Documentation: http://localhost:8000/docs")
    print("  • Streamlit UI: http://localhost:8501")
    print("  • Admin Login: admin / admin123")

    print("\n💡 Press Ctrl+C to stop all applications")

    try:
        # Wait for processes
        fastapi_process.wait()
        streamlit_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Stopping applications...")
        fastapi_process.terminate()
        streamlit_process.terminate()
        print("✅ Applications stopped")

if __name__ == "__main__":
    main()
