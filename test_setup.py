#!/usr/bin/env python3
"""
Quick test script to verify all dependencies are installed correctly
"""

import sys

def test_imports():
    """Test if all required modules can be imported"""
    errors = []
    
    try:
        import flask
        print("✅ Flask installed")
    except ImportError as e:
        errors.append("Flask")
        print(f"❌ Flask not installed: {e}")
    
    try:
        import flask_socketio
        print("✅ Flask-SocketIO installed")
    except ImportError as e:
        errors.append("Flask-SocketIO")
        print(f"❌ Flask-SocketIO not installed: {e}")
    
    try:
        import socketio
        print("✅ python-socketio installed")
    except ImportError as e:
        errors.append("python-socketio")
        print(f"❌ python-socketio not installed: {e}")
    
    try:
        import eventlet
        print("✅ eventlet installed")
    except ImportError as e:
        errors.append("eventlet")
        print(f"❌ eventlet not installed: {e}")
    
    if errors:
        print(f"\n❌ Missing dependencies: {', '.join(errors)}")
        print("Run: pip install -r requirements.txt")
        return False
    else:
        print("\n✅ All dependencies are installed correctly!")
        return True

def test_app_import():
    """Test if the app can be imported"""
    try:
        # Try to import the app
        sys.path.insert(0, '.')
        from app import app, socketio
        print("✅ app.py can be imported successfully")
        return True
    except Exception as e:
        print(f"❌ Error importing app.py: {e}")
        return False

def check_port():
    """Check if port 5000 is available"""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', 5000))
    sock.close()
    
    if result == 0:
        print("⚠️  Port 5000 is currently in use")
        print("   You may need to stop another application or use a different port")
        return False
    else:
        print("✅ Port 5000 is available")
        return True

if __name__ == "__main__":
    print("=" * 50)
    print("Testing Setup...")
    print("=" * 50)
    
    print("\n1. Checking Python version...")
    print(f"   Python {sys.version.split()[0]}")
    
    print("\n2. Checking dependencies...")
    deps_ok = test_imports()
    
    print("\n3. Checking app.py...")
    app_ok = test_app_import()
    
    print("\n4. Checking port availability...")
    port_ok = check_port()
    
    print("\n" + "=" * 50)
    if deps_ok and app_ok:
        print("✅ Setup looks good! You can run: python app.py")
    else:
        print("❌ Please fix the issues above before running the app")
    print("=" * 50)

