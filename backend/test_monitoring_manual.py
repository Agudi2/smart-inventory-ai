"""Manual test to verify monitoring endpoints work correctly."""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_health_endpoint():
    """Test the health check endpoint."""
    print("\n=== Testing /health endpoint ===")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body:\n{json.dumps(response.json(), indent=2)}")
        
        # Check correlation ID
        if 'X-Correlation-ID' in response.headers:
            print(f"✓ Correlation ID present: {response.headers['X-Correlation-ID']}")
        else:
            print("✗ Correlation ID missing")
            
    except Exception as e:
        print(f"Error: {e}")


def test_metrics_endpoint():
    """Test the metrics endpoint."""
    print("\n=== Testing /api/v1/metrics endpoint ===")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/metrics")
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body:\n{json.dumps(response.json(), indent=2)}")
        
        # Check correlation ID
        if 'X-Correlation-ID' in response.headers:
            print(f"✓ Correlation ID present: {response.headers['X-Correlation-ID']}")
        else:
            print("✗ Correlation ID missing")
            
    except Exception as e:
        print(f"Error: {e}")


def test_custom_correlation_id():
    """Test custom correlation ID."""
    print("\n=== Testing custom correlation ID ===")
    try:
        custom_id = "test-12345"
        response = requests.get(
            f"{BASE_URL}/health",
            headers={"X-Correlation-ID": custom_id}
        )
        print(f"Status Code: {response.status_code}")
        print(f"Sent Correlation ID: {custom_id}")
        print(f"Received Correlation ID: {response.headers.get('X-Correlation-ID')}")
        
        if response.headers.get('X-Correlation-ID') == custom_id:
            print("✓ Custom correlation ID preserved")
        else:
            print("✗ Custom correlation ID not preserved")
            
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    print("Manual Monitoring Endpoints Test")
    print("=" * 50)
    print("Make sure the server is running on http://localhost:8000")
    print("Start with: uvicorn app.main:app --reload")
    print("=" * 50)
    
    test_health_endpoint()
    test_metrics_endpoint()
    test_custom_correlation_id()
    
    print("\n" + "=" * 50)
    print("Test completed!")
