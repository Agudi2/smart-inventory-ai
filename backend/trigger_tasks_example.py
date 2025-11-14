"""Example script showing how to manually trigger Celery tasks."""

import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.tasks.ml_tasks import (
    train_model_for_product,
    train_all_models,
    generate_prediction,
    batch_generate_predictions
)
from app.tasks.alert_tasks import (
    check_low_stock_alerts,
    check_prediction_alerts,
    check_all_alerts,
    auto_resolve_alerts
)


def trigger_alert_check():
    """Trigger alert checking task."""
    print("Triggering alert check task...")
    result = check_all_alerts.delay()
    print(f"Task submitted: {result.id}")
    print(f"Status: {result.status}")
    
    # Wait for result (optional)
    print("Waiting for task to complete...")
    try:
        task_result = result.get(timeout=60)
        print(f"Task completed successfully!")
        print(f"Result: {task_result}")
    except Exception as e:
        print(f"Task failed or timed out: {str(e)}")


def trigger_ml_training():
    """Trigger ML model training for all products."""
    print("Triggering ML model training task...")
    result = train_all_models.delay()
    print(f"Task submitted: {result.id}")
    print(f"Status: {result.status}")
    
    print("\nNote: This task may take a long time to complete.")
    print("You can check the status later using the task ID.")
    
    # Don't wait for result as it may take a long time
    return result.id


def trigger_prediction_for_product(product_id: str):
    """Trigger prediction generation for a specific product."""
    print(f"Triggering prediction for product {product_id}...")
    result = generate_prediction.delay(product_id)
    print(f"Task submitted: {result.id}")
    print(f"Status: {result.status}")
    
    # Wait for result
    print("Waiting for task to complete...")
    try:
        task_result = result.get(timeout=120)
        print(f"Task completed successfully!")
        print(f"Result: {task_result}")
    except Exception as e:
        print(f"Task failed or timed out: {str(e)}")


def check_task_status(task_id: str):
    """Check the status of a task."""
    from celery.result import AsyncResult
    from app.core.celery_app import celery_app
    
    result = AsyncResult(task_id, app=celery_app)
    print(f"Task ID: {task_id}")
    print(f"Status: {result.status}")
    
    if result.ready():
        print(f"Result: {result.result}")
    else:
        print("Task is still running...")


def main():
    """Main function with interactive menu."""
    print("=" * 60)
    print("Celery Task Trigger Example")
    print("=" * 60)
    print("\nThis script demonstrates how to manually trigger Celery tasks.")
    print("\nMake sure:")
    print("1. Redis is running")
    print("2. Celery worker is running")
    print("3. Database is accessible")
    
    print("\n" + "=" * 60)
    print("Available Actions:")
    print("=" * 60)
    print("1. Trigger alert check (quick)")
    print("2. Trigger ML model training (slow)")
    print("3. Trigger prediction for a product")
    print("4. Check task status")
    print("5. Exit")
    
    while True:
        print("\n" + "-" * 60)
        choice = input("Enter your choice (1-5): ").strip()
        
        if choice == "1":
            trigger_alert_check()
        
        elif choice == "2":
            task_id = trigger_ml_training()
            print(f"\nSave this task ID to check status later: {task_id}")
        
        elif choice == "3":
            product_id = input("Enter product UUID: ").strip()
            if product_id:
                trigger_prediction_for_product(product_id)
            else:
                print("Invalid product ID")
        
        elif choice == "4":
            task_id = input("Enter task ID: ").strip()
            if task_id:
                check_task_status(task_id)
            else:
                print("Invalid task ID")
        
        elif choice == "5":
            print("Exiting...")
            break
        
        else:
            print("Invalid choice. Please enter 1-5.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting...")
        sys.exit(0)
