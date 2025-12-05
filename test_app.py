#!/usr/bin/env python3
"""
Simple test script to verify the GSM C2 Dashboard application
Checks imports and basic configurations
"""

import sys
import os

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test all module imports"""
    print("🔍 Testing module imports...")
    
    try:
        from app.config import settings
        print("✅ Config module OK")
        
        from app.models.schemas import (
            StatusResponse,
            SubscriberResponse,
            EncryptionConfigRequest,
            SMSSpoofRequest
        )
        print("✅ Schemas module OK")
        
        from app.models.database import db_manager
        print("✅ Database module OK")
        
        from app.services.vty_client import VTYClient
        print("✅ VTY Client OK")
        
        from app.services.osmocom_service import osmocom_service
        print("✅ Osmocom Service OK")
        
        from app.services.sms_service import sms_service
        print("✅ SMS Service OK")
        
        from app.services.log_monitor import LogMonitor
        print("✅ Log Monitor OK")
        
        from app.api.routes import router
        print("✅ API Routes OK")
        
        from app.main import app
        print("✅ Main Application OK")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_configuration():
    """Test configuration loading"""
    print("\n🔧 Testing configuration...")
    
    try:
        from app.config import settings
        
        print(f"  VTY Host: {settings.vty_host}")
        print(f"  VTY MSC Port: {settings.vty_msc_port}")
        print(f"  VTY BTS Port: {settings.vty_bts_port}")
        print(f"  HLR Database: {settings.hlr_database_path}")
        print(f"  Log Path: {settings.osmocom_log_path}")
        print(f"  App Port: {settings.app_port}")
        
        print("✅ Configuration loaded successfully")
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


def test_pydantic_models():
    """Test Pydantic model validation"""
    print("\n📋 Testing Pydantic models...")
    
    try:
        from app.models.schemas import SMSSpoofRequest, EncryptionConfigRequest
        
        # Test valid IMSI
        sms_request = SMSSpoofRequest(
            imsi="001010000000001",
            sender_id="TEST",
            message="Hello World"
        )
        print(f"✅ Valid IMSI accepted: {sms_request.imsi}")
        
        # Test encryption config
        enc_request = EncryptionConfigRequest(mode="A5/0")
        print(f"✅ Valid encryption mode: {enc_request.mode}")
        
        # Test invalid IMSI
        try:
            invalid_sms = SMSSpoofRequest(
                imsi="123",  # Too short
                sender_id="TEST",
                message="Test"
            )
            print("❌ Invalid IMSI was accepted (should have failed)")
            return False
        except Exception:
            print("✅ Invalid IMSI correctly rejected")
        
        return True
    except Exception as e:
        print(f"❌ Model validation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_app_initialization():
    """Test FastAPI app initialization"""
    print("\n🚀 Testing FastAPI app initialization...")
    
    try:
        from app.main import app
        
        print(f"  App Title: {app.title}")
        print(f"  App Version: {app.version}")
        print(f"  Routes: {len(app.routes)}")
        
        # List endpoints
        print("\n  Available endpoints:")
        for route in app.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                methods = ', '.join(route.methods) if route.methods else 'N/A'
                print(f"    {methods:8} {route.path}")
        
        print("\n✅ FastAPI app initialized successfully")
        return True
    except Exception as e:
        print(f"❌ App initialization test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("GSM C2 Dashboard - Verification Tests")
    print("=" * 60)
    
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("Configuration", test_configuration()))
    results.append(("Pydantic Models", test_pydantic_models()))
    results.append(("App Initialization", test_app_initialization()))
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:20} {status}")
    
    print("=" * 60)
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n🎉 All tests passed! Application is ready to run.")
        print("\nTo start the server, run:")
        print("  python -m app.main")
        print("\nOr with uvicorn:")
        print("  ./venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
