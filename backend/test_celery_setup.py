"""Test script to verify Celery setup and task execution."""

import sys
import time
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.core.celery_app import celery_app
from app.tasks.ml_tasks import train_all_models, batch_generate_predictions
from app.tasks.alert_tasks import check_all_alerts, auto_resolve_alerts


def test_celery_connection():
    """Test Celery broker connection."""
    print("Testing Celery broker connection...")
    try:
        # Inspect active workers
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        
        if active_workers:
            print(f"✓ Connected to Celery broker")
            print(f"  Active workers: {list(active_workers.keys())}")
            return True
        else:
            print("✗ No active workers found")
            print("  Make sure Celery worker is running:")
            print("  celery -A app.core.celery_app:celery_app worker --loglevel=info")
            return False
    except Exception as e:
        print(f"✗ Failed to connect to Celery broker: {str(e)}")
        print("  Make sure Redis is running:")
        print("  docker run -d -p 6379:6379 redis:7-alpine")
        return False


def test_task_registration():
    """Test that all tasks are properly registered."""
    print("\nTesting task registration...")
    
    expected_tasks = [
        "app.tasks.ml_tasks.train_model_for_product",
        "app.tasks.ml_tasks.train_all_models",
        "app.tasks.ml_tasks.generate_prediction",
        "app.tasks.ml_tasks.batch_generate_predictions",
        "app.tasks.alert_tasks.check_low_stock_alerts",
        "app.tasks.alert_tasks.check_prediction_alerts",
        "app.tasks.alert_tasks.check_all_alerts",
        "app.tasks.alert_tasks.auto_resolve_alerts",
        "app.tasks.alert_tasks.send_alert_notification",
    ]
    
    try:
        inspect = celery_app.control.inspect()
        registered_tasks = inspect.registered()
        
        if not registered_tasks:
            print("✗ No registered tasks found")
            return False
        
        # Get all registered task names from all workers
        all_registered = set()
        for worker_tasks in registered_tasks.values():
            all_registered.update(worker_tasks)
        
        print(f"✓ Found {len(all_registered)} registered tasks")
        
        # Check if expected tasks are registered
        missing_tasks = []
        for task in expected_tasks:
            if task not in all_registered:
                missing_tasks.append(task)
        
        if missing_tasks:
            print(f"✗ Missing tasks:")
            for task in missing_tasks:
                print(f"  - {task}")
            return False
        else:
            print("✓ All expected tasks are registered")
            return True
            
    except Exception as e:
        print(f"✗ Failed to check task registration: {str(e)}")
        return False


def test_beat_schedule():
    """Test Celery Beat schedule configuration."""
    print("\nTesting Celery Beat schedule...")
    
    schedule = celery_app.conf.beat_schedule
    
    if not schedule:
        print("✗ No scheduled tasks found")
        return False
    
    print(f"✓ Found {len(schedule)} scheduled tasks:")
    
    for task_name, task_config in schedule.items():
        task = task_config.get('task')
        schedule_info = task_config.get('schedule')
        print(f"  - {task_name}")
        print(f"    Task: {task}")
        print(f"    Schedule: {schedule_info}")
    
    return True


def test_task_execution():
    """Test executing a simple task."""
    print("\nTesting task execution...")
    print("Note: This requires a running Celery worker and database connection")
    
    try:
        # Try to execute a simple alert check task
        print("Triggering check_all_alerts task...")
        result = check_all_alerts.delay()
        
        print(f"✓ Task submitted successfully")
        print(f"  Task ID: {result.id}")
        print(f"  Status: {result.status}")
        
        # Wait for result (with timeout)
        print("  Waiting for task to complete (timeout: 30 seconds)...")
        try:
            task_result = result.get(timeout=30)
            print(f"✓ Task completed successfully")
            print(f"  Result: {task_result}")
            return True
        except Exception as e:
            print(f"✗ Task execution failed or timed out: {str(e)}")
            print(f"  Task status: {result.status}")
            return False
            
    except Exception as e:
        print(f"✗ Failed to submit task: {str(e)}")
        return False


def main():
    """Run all Celery setup tests."""
    print("=" * 60)
    print("Celery Setup Verification")
    print("=" * 60)
    
    results = []
    
    # Test 1: Broker connection
    results.append(("Broker Connection", test_celery_connection()))
    
    # Test 2: Task registration (only if broker is connected)
    if results[0][1]:
        results.append(("Task Registration", test_task_registration()))
    
    # Test 3: Beat schedule
    results.append(("Beat Schedule", test_beat_schedule()))
    
    # Test 4: Task execution (optional, requires worker and database)
    print("\n" + "=" * 60)
    response = input("Do you want to test task execution? (requires worker and database) [y/N]: ")
    if response.lower() == 'y':
        results.append(("Task Execution", test_task_execution()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    total_tests = len(results)
    passed_tests = sum(1 for _, passed in results if passed)
    
    print(f"\nTotal: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("\n✓ All tests passed! Celery is properly configured.")
        return 0
    else:
        print("\n✗ Some tests failed. Please check the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
