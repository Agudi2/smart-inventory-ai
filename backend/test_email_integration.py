"""Integration test for email notification system."""

import sys
from pathlib import Path
from datetime import datetime
from uuid import uuid4

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import settings
from app.services.email_service import EmailService
from app.models.alert import Alert
from app.models.product import Product


def test_email_service_initialization():
    """Test that EmailService initializes correctly."""
    print("Testing EmailService initialization...")
    
    try:
        email_service = EmailService()
        print(f"✅ EmailService initialized")
        print(f"   - SMTP Host: {email_service.smtp_host}")
        print(f"   - SMTP Port: {email_service.smtp_port}")
        print(f"   - From Email: {email_service.from_email}")
        print(f"   - Enabled: {email_service.enabled}")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize EmailService: {str(e)}")
        return False


def test_email_template_rendering():
    """Test that email templates can be rendered."""
    print("\nTesting email template rendering...")
    
    try:
        email_service = EmailService()
        
        # Create mock product and alert objects
        mock_product = Product(
            id=uuid4(),
            sku="TEST-001",
            name="Test Product",
            category="Test Category",
            current_stock=5,
            reorder_threshold=10,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        mock_alert = Alert(
            id=uuid4(),
            product_id=mock_product.id,
            alert_type="low_stock",
            severity="warning",
            message="Test alert message",
            status="active",
            created_at=datetime.utcnow()
        )
        mock_alert.product = mock_product
        
        # Test low stock template
        template = email_service.jinja_env.get_template("low_stock_alert.html")
        html = template.render(
            alert=mock_alert,
            product=mock_product,
            severity_emoji="⚠️",
            app_name=settings.app_name
        )
        
        if html and len(html) > 100:
            print("✅ Low stock template rendered successfully")
            print(f"   - Template length: {len(html)} characters")
        else:
            print("❌ Low stock template rendering failed")
            return False
        
        # Test predicted depletion template
        mock_alert.alert_type = "predicted_depletion"
        template = email_service.jinja_env.get_template("predicted_depletion_alert.html")
        html = template.render(
            alert=mock_alert,
            product=mock_product,
            severity_emoji="🔴",
            app_name=settings.app_name
        )
        
        if html and len(html) > 100:
            print("✅ Predicted depletion template rendered successfully")
            print(f"   - Template length: {len(html)} characters")
        else:
            print("❌ Predicted depletion template rendering failed")
            return False
        
        # Test generic template
        template = email_service.jinja_env.get_template("generic_alert.html")
        html = template.render(
            alert=mock_alert,
            product=mock_product,
            severity_emoji="⚠️",
            app_name=settings.app_name
        )
        
        if html and len(html) > 100:
            print("✅ Generic alert template rendered successfully")
            print(f"   - Template length: {len(html)} characters")
        else:
            print("❌ Generic alert template rendering failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Template rendering failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_text_body_generation():
    """Test plain text email body generation."""
    print("\nTesting plain text body generation...")
    
    try:
        email_service = EmailService()
        
        # Create mock product and alert
        mock_product = Product(
            id=uuid4(),
            sku="TEST-001",
            name="Test Product",
            category="Test Category",
            current_stock=5,
            reorder_threshold=10,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        mock_alert = Alert(
            id=uuid4(),
            product_id=mock_product.id,
            alert_type="low_stock",
            severity="critical",
            message="Test alert message",
            status="active",
            created_at=datetime.utcnow()
        )
        mock_alert.product = mock_product
        
        # Generate text body
        text_body = email_service._create_text_body(mock_alert)
        
        if text_body and len(text_body) > 50:
            print("✅ Plain text body generated successfully")
            print(f"   - Body length: {len(text_body)} characters")
            print(f"   - Contains product name: {'Test Product' in text_body}")
            print(f"   - Contains SKU: {'TEST-001' in text_body}")
            return True
        else:
            print("❌ Plain text body generation failed")
            return False
            
    except Exception as e:
        print(f"❌ Text body generation failed: {str(e)}")
        return False


def test_email_disabled_behavior():
    """Test that email service behaves correctly when disabled."""
    print("\nTesting email disabled behavior...")
    
    try:
        # Temporarily disable email
        original_enabled = settings.email_notifications_enabled
        settings.email_notifications_enabled = False
        
        email_service = EmailService()
        
        # Try to send email
        result = email_service.send_email(
            to_emails=["test@example.com"],
            subject="Test",
            html_body="<p>Test</p>"
        )
        
        # Restore original setting
        settings.email_notifications_enabled = original_enabled
        
        if result is False:
            print("✅ Email service correctly returns False when disabled")
            return True
        else:
            print("❌ Email service should return False when disabled")
            return False
            
    except Exception as e:
        print(f"❌ Disabled behavior test failed: {str(e)}")
        settings.email_notifications_enabled = original_enabled
        return False


def run_all_tests():
    """Run all email integration tests."""
    print("=" * 60)
    print("Email Notification System Integration Tests")
    print("=" * 60)
    print()
    
    tests = [
        ("EmailService Initialization", test_email_service_initialization),
        ("Email Template Rendering", test_email_template_rendering),
        ("Plain Text Body Generation", test_text_body_generation),
        ("Email Disabled Behavior", test_email_disabled_behavior),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {str(e)}")
            results.append((test_name, False))
        print()
    
    # Summary
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print(f"⚠️  {total - passed} test(s) failed")
    
    print("=" * 60)
    print()
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
