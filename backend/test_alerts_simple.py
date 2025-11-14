"""Simple test to verify alert system implementation compiles correctly."""

import sys
sys.path.insert(0, '.')

print("Testing imports...")

# Test alert model
from app.models.alert import Alert
print("✓ Alert model imported successfully")

# Test alert schemas
from app.schemas.alert import (
    AlertBase,
    AlertCreate,
    AlertResponse,
    AlertAcknowledge,
    AlertResolve,
    AlertSettingsResponse,
    AlertSettingsUpdate
)
print("✓ Alert schemas imported successfully")

# Test alert service
from app.services.alert_service import AlertService
print("✓ Alert service imported successfully")

# Test alert routes
from app.api.routes import alerts
print("✓ Alert routes imported successfully")

# Test exception
from app.core.exceptions import AlertNotFoundException
print("✓ AlertNotFoundException imported successfully")

# Test main app includes alerts
from app.main import app
print("✓ Main app imported successfully")

# Test schema validation
print("\nTesting schema validation...")
try:
    from uuid import uuid4
    
    # Valid alert creation
    alert_create = AlertCreate(
        product_id=uuid4(),
        alert_type="low_stock",
        severity="warning",
        message="Test alert message"
    )
    print(f"  Valid alert: {alert_create.alert_type} - {alert_create.severity}")
    print("✓ Valid alert schema accepted")
except Exception as e:
    print(f"✗ Valid alert schema rejected: {e}")
    sys.exit(1)

try:
    # Valid alert settings update
    settings_update = AlertSettingsUpdate(
        alert_threshold_days=14,
        low_stock_enabled=True,
        predicted_depletion_enabled=False
    )
    print(f"  Valid settings: threshold={settings_update.alert_threshold_days} days")
    print("✓ Valid settings schema accepted")
except Exception as e:
    print(f"✗ Valid settings schema rejected: {e}")
    sys.exit(1)

# Test API routes are registered
print("\nTesting API routes...")
routes = [route.path for route in app.routes]
alert_routes = [r for r in routes if '/alerts' in r]
print(f"  Found {len(alert_routes)} alert routes:")
for route in alert_routes:
    print(f"    - {route}")

expected_routes = [
    '/api/v1/alerts',
    '/api/v1/alerts/{alert_id}/acknowledge',
    '/api/v1/alerts/{alert_id}/resolve',
    '/api/v1/alerts/settings'
]

for expected in expected_routes:
    if any(expected in route for route in alert_routes):
        print(f"✓ Route {expected} registered")
    else:
        print(f"✗ Route {expected} NOT found")
        sys.exit(1)

print("\n" + "="*50)
print("All alert system tests passed successfully!")
print("="*50)
