"""
Database seed script for Smart Inventory Management System.

This script populates the database with sample data including:
- Products across multiple categories
- Inventory transactions (90 days of historical data)
- Vendors with price variations
- Users with different roles
"""

import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal
import random
from typing import List

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, init_db
from app.core.security import hash_password
from app.models import (
    Product,
    InventoryTransaction,
    Vendor,
    VendorPrice,
    User,
    Alert,
)


# Sample data definitions
CATEGORIES = [
    "Electronics",
    "Office Supplies",
    "Furniture",
    "Cleaning Supplies",
    "Food & Beverages",
    "Safety Equipment",
]

SAMPLE_PRODUCTS = [
    # Electronics
    {"sku": "ELEC-001", "name": "Wireless Mouse", "category": "Electronics", "stock": 45, "threshold": 20, "cost": 25.99, "barcode": "1234567890123"},
    {"sku": "ELEC-002", "name": "USB-C Cable", "category": "Electronics", "stock": 120, "threshold": 50, "cost": 12.50, "barcode": "1234567890124"},
    {"sku": "ELEC-003", "name": "Laptop Stand", "category": "Electronics", "stock": 15, "threshold": 10, "cost": 45.00, "barcode": "1234567890125"},
    {"sku": "ELEC-004", "name": "Webcam HD", "category": "Electronics", "stock": 8, "threshold": 15, "cost": 89.99, "barcode": "1234567890126"},
    {"sku": "ELEC-005", "name": "Keyboard Mechanical", "category": "Electronics", "stock": 22, "threshold": 12, "cost": 129.99, "barcode": "1234567890127"},
    
    # Office Supplies
    {"sku": "OFF-001", "name": "A4 Paper Ream", "category": "Office Supplies", "stock": 200, "threshold": 100, "cost": 8.99, "barcode": "2234567890123"},
    {"sku": "OFF-002", "name": "Blue Pens (Pack of 10)", "category": "Office Supplies", "stock": 75, "threshold": 30, "cost": 5.99, "barcode": "2234567890124"},
    {"sku": "OFF-003", "name": "Sticky Notes", "category": "Office Supplies", "stock": 150, "threshold": 50, "cost": 3.50, "barcode": "2234567890125"},
    {"sku": "OFF-004", "name": "Stapler", "category": "Office Supplies", "stock": 35, "threshold": 15, "cost": 12.99, "barcode": "2234567890126"},
    {"sku": "OFF-005", "name": "File Folders (Box)", "category": "Office Supplies", "stock": 60, "threshold": 25, "cost": 18.50, "barcode": "2234567890127"},
    
    # Furniture
    {"sku": "FURN-001", "name": "Office Chair", "category": "Furniture", "stock": 12, "threshold": 5, "cost": 199.99, "barcode": "3234567890123"},
    {"sku": "FURN-002", "name": "Standing Desk", "category": "Furniture", "stock": 6, "threshold": 3, "cost": 449.99, "barcode": "3234567890124"},
    {"sku": "FURN-003", "name": "Bookshelf", "category": "Furniture", "stock": 8, "threshold": 4, "cost": 129.99, "barcode": "3234567890125"},
    {"sku": "FURN-004", "name": "Filing Cabinet", "category": "Furniture", "stock": 5, "threshold": 2, "cost": 179.99, "barcode": "3234567890126"},
    
    # Cleaning Supplies
    {"sku": "CLEAN-001", "name": "Disinfectant Spray", "category": "Cleaning Supplies", "stock": 85, "threshold": 40, "cost": 6.99, "barcode": "4234567890123"},
    {"sku": "CLEAN-002", "name": "Paper Towels (12-pack)", "category": "Cleaning Supplies", "stock": 110, "threshold": 50, "cost": 15.99, "barcode": "4234567890124"},
    {"sku": "CLEAN-003", "name": "Trash Bags (Box)", "category": "Cleaning Supplies", "stock": 95, "threshold": 30, "cost": 12.50, "barcode": "4234567890125"},
    {"sku": "CLEAN-004", "name": "Glass Cleaner", "category": "Cleaning Supplies", "stock": 42, "threshold": 20, "cost": 4.99, "barcode": "4234567890126"},
    
    # Food & Beverages
    {"sku": "FOOD-001", "name": "Coffee Beans (1kg)", "category": "Food & Beverages", "stock": 28, "threshold": 15, "cost": 24.99, "barcode": "5234567890123"},
    {"sku": "FOOD-002", "name": "Tea Bags (Box of 100)", "category": "Food & Beverages", "stock": 45, "threshold": 20, "cost": 8.99, "barcode": "5234567890124"},
    {"sku": "FOOD-003", "name": "Bottled Water (24-pack)", "category": "Food & Beverages", "stock": 65, "threshold": 30, "cost": 6.99, "barcode": "5234567890125"},
    {"sku": "FOOD-004", "name": "Snack Mix (Box)", "category": "Food & Beverages", "stock": 38, "threshold": 25, "cost": 19.99, "barcode": "5234567890126"},
    
    # Safety Equipment
    {"sku": "SAFE-001", "name": "First Aid Kit", "category": "Safety Equipment", "stock": 18, "threshold": 10, "cost": 34.99, "barcode": "6234567890123"},
    {"sku": "SAFE-002", "name": "Fire Extinguisher", "category": "Safety Equipment", "stock": 10, "threshold": 5, "cost": 49.99, "barcode": "6234567890124"},
    {"sku": "SAFE-003", "name": "Safety Goggles", "category": "Safety Equipment", "stock": 55, "threshold": 20, "cost": 8.99, "barcode": "6234567890125"},
    {"sku": "SAFE-004", "name": "Hard Hat", "category": "Safety Equipment", "stock": 25, "threshold": 12, "cost": 22.99, "barcode": "6234567890126"},
]

SAMPLE_VENDORS = [
    {"name": "TechSupply Co.", "email": "sales@techsupply.com", "phone": "+1-555-0101", "address": "123 Tech Street, San Francisco, CA 94105"},
    {"name": "Office Depot Plus", "email": "orders@officedepotplus.com", "phone": "+1-555-0102", "address": "456 Business Ave, New York, NY 10001"},
    {"name": "Furniture World", "email": "info@furnitureworld.com", "phone": "+1-555-0103", "address": "789 Design Blvd, Chicago, IL 60601"},
    {"name": "CleanPro Supplies", "email": "contact@cleanpro.com", "phone": "+1-555-0104", "address": "321 Clean Lane, Austin, TX 78701"},
    {"name": "Global Distributors", "email": "sales@globaldist.com", "phone": "+1-555-0105", "address": "654 Trade Center, Seattle, WA 98101"},
    {"name": "Budget Wholesale", "email": "orders@budgetwholesale.com", "phone": "+1-555-0106", "address": "987 Discount Dr, Miami, FL 33101"},
]

SAMPLE_USERS = [
    {"email": "admin@inventory.com", "password": "admin123", "full_name": "Admin User", "role": "admin"},
    {"email": "manager@inventory.com", "password": "manager123", "full_name": "Manager User", "role": "manager"},
    {"email": "user@inventory.com", "password": "user123", "full_name": "Regular User", "role": "user"},
    {"email": "warehouse@inventory.com", "password": "warehouse123", "full_name": "Warehouse Staff", "role": "user"},
]


def create_users(db: Session) -> List[User]:
    """Create sample users with different roles."""
    print("Creating users...")
    users = []
    
    for user_data in SAMPLE_USERS:
        user = User(
            email=user_data["email"],
            hashed_password=hash_password(user_data["password"]),
            full_name=user_data["full_name"],
            role=user_data["role"],
            is_active=True
        )
        db.add(user)
        users.append(user)
    
    db.commit()
    print(f"✓ Created {len(users)} users")
    return users


def create_vendors(db: Session) -> List[Vendor]:
    """Create sample vendors."""
    print("Creating vendors...")
    vendors = []
    
    for vendor_data in SAMPLE_VENDORS:
        vendor = Vendor(
            name=vendor_data["name"],
            contact_email=vendor_data["email"],
            contact_phone=vendor_data["phone"],
            address=vendor_data["address"]
        )
        db.add(vendor)
        vendors.append(vendor)
    
    db.commit()
    print(f"✓ Created {len(vendors)} vendors")
    return vendors


def create_products(db: Session) -> List[Product]:
    """Create sample products."""
    print("Creating products...")
    products = []
    
    for product_data in SAMPLE_PRODUCTS:
        product = Product(
            sku=product_data["sku"],
            name=product_data["name"],
            category=product_data["category"],
            current_stock=product_data["stock"],
            reorder_threshold=product_data["threshold"],
            unit_cost=Decimal(str(product_data["cost"])),
            barcode=product_data["barcode"]
        )
        db.add(product)
        products.append(product)
    
    db.commit()
    print(f"✓ Created {len(products)} products")
    return products


def create_vendor_prices(db: Session, vendors: List[Vendor], products: List[Product]) -> None:
    """Create vendor price relationships with variations."""
    print("Creating vendor prices...")
    vendor_prices = []
    
    # Each product gets 2-4 vendors with different prices
    for product in products:
        num_vendors = random.randint(2, min(4, len(vendors)))
        selected_vendors = random.sample(vendors, num_vendors)
        
        base_price = float(product.unit_cost) if product.unit_cost else 10.0
        
        for i, vendor in enumerate(selected_vendors):
            # Create price variation (±20% from base cost)
            price_variation = random.uniform(0.8, 1.2)
            unit_price = Decimal(str(round(base_price * price_variation, 2)))
            
            vendor_price = VendorPrice(
                vendor_id=vendor.id,
                product_id=product.id,
                unit_price=unit_price,
                lead_time_days=random.randint(3, 14),
                minimum_order_quantity=random.choice([1, 5, 10, 20]),
                last_updated=datetime.utcnow() - timedelta(days=random.randint(0, 30))
            )
            db.add(vendor_price)
            vendor_prices.append(vendor_price)
    
    db.commit()
    print(f"✓ Created {len(vendor_prices)} vendor price records")


def create_inventory_transactions(db: Session, products: List[Product], users: List[User]) -> None:
    """Generate 90 days of historical inventory transactions."""
    print("Creating inventory transactions (90 days of history)...")
    transactions = []
    
    # Start date: 90 days ago
    start_date = datetime.utcnow() - timedelta(days=90)
    
    for product in products:
        # Simulate realistic stock movements
        current_stock = 0  # Start from 0
        transaction_date = start_date
        
        # Initial stock addition
        initial_stock = product.current_stock + random.randint(50, 200)
        transaction = InventoryTransaction(
            product_id=product.id,
            transaction_type="addition",
            quantity=initial_stock,
            previous_stock=0,
            new_stock=initial_stock,
            reason="Initial stock",
            user_id=random.choice(users).id,
            created_at=transaction_date
        )
        db.add(transaction)
        transactions.append(transaction)
        current_stock = initial_stock
        
        # Generate transactions over 90 days
        days_passed = 0
        while days_passed < 90:
            # Random number of days until next transaction (1-5 days)
            days_until_next = random.randint(1, 5)
            transaction_date += timedelta(days=days_until_next)
            days_passed += days_until_next
            
            if days_passed >= 90:
                break
            
            # Determine transaction type (70% removal, 30% addition)
            if random.random() < 0.7 and current_stock > 10:
                # Removal transaction
                max_removal = min(current_stock - 5, 30)
                quantity = random.randint(1, max(1, max_removal))
                transaction_type = "removal"
                new_stock = current_stock - quantity
                reason = random.choice([
                    "Sale",
                    "Customer order",
                    "Internal use",
                    "Damaged goods",
                    "Sample"
                ])
            else:
                # Addition transaction
                quantity = random.randint(10, 100)
                transaction_type = "addition"
                new_stock = current_stock + quantity
                reason = random.choice([
                    "Restock",
                    "New shipment",
                    "Vendor delivery",
                    "Return"
                ])
            
            transaction = InventoryTransaction(
                product_id=product.id,
                transaction_type=transaction_type,
                quantity=quantity,
                previous_stock=current_stock,
                new_stock=new_stock,
                reason=reason,
                user_id=random.choice(users).id,
                created_at=transaction_date
            )
            db.add(transaction)
            transactions.append(transaction)
            current_stock = new_stock
        
        # Final adjustment to match current stock
        if current_stock != product.current_stock:
            adjustment = product.current_stock - current_stock
            transaction = InventoryTransaction(
                product_id=product.id,
                transaction_type="adjustment",
                quantity=abs(adjustment),
                previous_stock=current_stock,
                new_stock=product.current_stock,
                reason="Stock reconciliation",
                user_id=random.choice(users).id,
                created_at=datetime.utcnow()
            )
            db.add(transaction)
            transactions.append(transaction)
    
    db.commit()
    print(f"✓ Created {len(transactions)} inventory transactions")


def create_sample_alerts(db: Session, products: List[Product]) -> None:
    """Create sample alerts for low stock products."""
    print("Creating sample alerts...")
    alerts = []
    
    # Find products with low stock
    low_stock_products = [p for p in products if p.current_stock < p.reorder_threshold]
    
    for product in low_stock_products[:5]:  # Create alerts for first 5 low stock items
        alert = Alert(
            product_id=product.id,
            alert_type="low_stock",
            severity="critical" if product.current_stock < p.reorder_threshold * 0.5 else "warning",
            message=f"Stock level for {product.name} is below reorder threshold. Current: {product.current_stock}, Threshold: {product.reorder_threshold}",
            status="active",
            created_at=datetime.utcnow() - timedelta(hours=random.randint(1, 48))
        )
        db.add(alert)
        alerts.append(alert)
    
    db.commit()
    print(f"✓ Created {len(alerts)} sample alerts")


def seed_database():
    """Main function to seed the database with all sample data."""
    print("\n" + "="*60)
    print("Smart Inventory Management System - Database Seeding")
    print("="*60 + "\n")
    
    # Initialize database
    print("Initializing database...")
    init_db()
    print("✓ Database initialized\n")
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Create all sample data
        users = create_users(db)
        vendors = create_vendors(db)
        products = create_products(db)
        create_vendor_prices(db, vendors, products)
        create_inventory_transactions(db, products, users)
        create_sample_alerts(db, products)
        
        print("\n" + "="*60)
        print("Database seeding completed successfully!")
        print("="*60)
        print("\nSample Login Credentials:")
        print("-" * 60)
        for user_data in SAMPLE_USERS:
            print(f"  {user_data['role'].upper():12} | {user_data['email']:30} | {user_data['password']}")
        print("-" * 60)
        print(f"\nTotal Records Created:")
        print(f"  - Users: {len(users)}")
        print(f"  - Vendors: {len(vendors)}")
        print(f"  - Products: {len(products)}")
        print(f"  - Categories: {len(CATEGORIES)}")
        print("\n")
        
    except Exception as e:
        print(f"\n❌ Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
