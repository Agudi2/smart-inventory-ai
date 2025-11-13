"""Simple test to verify barcode scanning implementation compiles correctly."""

import sys
sys.path.insert(0, '.')

print("Testing imports...")

# Test barcode schemas
from app.schemas.barcode import (
    BarcodeScanRequest,
    BarcodeProductInfo,
    BarcodeScanResponse,
    BarcodeLinkRequest,
    BarcodeLinkResponse
)
print("✓ Barcode schemas imported successfully")

# Test barcode service
from app.services.barcode_service import BarcodeService
print("✓ Barcode service imported successfully")

# Test barcode routes
from app.api.routes import barcode
print("✓ Barcode routes imported successfully")

# Test main app with barcode routes registered
from app.main import app
print("✓ Main app with barcode routes imported successfully")

# Test schema validation
print("\nTesting schema validation...")
try:
    # Valid barcode scan request
    scan_request = BarcodeScanRequest(barcode="1234567890123")
    print(f"  Valid scan request: {scan_request.barcode}")
    print("✓ Valid scan request schema accepted")
    
    # Valid barcode link request
    from uuid import uuid4
    link_request = BarcodeLinkRequest(
        barcode="9876543210987",
        product_id=uuid4()
    )
    print(f"  Valid link request: {link_request.barcode}")
    print("✓ Valid link request schema accepted")
    
    # Valid external product info
    external_info = BarcodeProductInfo(
        barcode="1234567890123",
        title="Test Product",
        brand="Test Brand",
        category="Electronics",
        description="A test product",
        images=["http://example.com/image.jpg"]
    )
    print(f"  Valid external info: {external_info.title}")
    print("✓ Valid external info schema accepted")
    
except Exception as e:
    print(f"✗ Schema validation failed: {e}")
    sys.exit(1)

# Test that routes are registered
print("\nTesting route registration...")
try:
    routes = [route.path for route in app.routes]
    
    expected_routes = [
        "/api/v1/barcode/scan",
        "/api/v1/barcode/lookup/{code}",
        "/api/v1/barcode/link"
    ]
    
    for expected_route in expected_routes:
        if expected_route in routes:
            print(f"  ✓ Route registered: {expected_route}")
        else:
            print(f"  ✗ Route missing: {expected_route}")
            sys.exit(1)
    
    print("✓ All barcode routes registered successfully")
    
except Exception as e:
    print(f"✗ Route registration check failed: {e}")
    sys.exit(1)

print("\n" + "="*50)
print("✓ All barcode implementation tests passed!")
print("="*50)
