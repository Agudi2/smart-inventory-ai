"""
Validation script for seed data.
Checks that all seed data is properly structured before running the seed script.
"""

import sys
from seed_data import SAMPLE_PRODUCTS, SAMPLE_VENDORS, SAMPLE_USERS, CATEGORIES


def validate_products():
    """Validate product data structure."""
    print("Validating products...")
    errors = []
    
    skus = set()
    barcodes = set()
    
    for i, product in enumerate(SAMPLE_PRODUCTS):
        # Check required fields
        required_fields = ["sku", "name", "category", "stock", "threshold", "cost"]
        for field in required_fields:
            if field not in product:
                errors.append(f"Product {i}: Missing required field '{field}'")
        
        # Check for duplicate SKUs
        if "sku" in product:
            if product["sku"] in skus:
                errors.append(f"Product {i}: Duplicate SKU '{product['sku']}'")
            skus.add(product["sku"])
        
        # Check for duplicate barcodes
        if "barcode" in product:
            if product["barcode"] in barcodes:
                errors.append(f"Product {i}: Duplicate barcode '{product['barcode']}'")
            barcodes.add(product["barcode"])
        
        # Check category is valid
        if "category" in product and product["category"] not in CATEGORIES:
            errors.append(f"Product {i}: Invalid category '{product['category']}'")
        
        # Check numeric values
        if "stock" in product and not isinstance(product["stock"], int):
            errors.append(f"Product {i}: Stock must be an integer")
        
        if "threshold" in product and not isinstance(product["threshold"], int):
            errors.append(f"Product {i}: Threshold must be an integer")
    
    if errors:
        print(f"  ❌ Found {len(errors)} errors:")
        for error in errors:
            print(f"    - {error}")
        return False
    else:
        print(f"  ✓ All {len(SAMPLE_PRODUCTS)} products are valid")
        return True


def validate_vendors():
    """Validate vendor data structure."""
    print("Validating vendors...")
    errors = []
    
    for i, vendor in enumerate(SAMPLE_VENDORS):
        # Check required fields
        required_fields = ["name", "email", "phone", "address"]
        for field in required_fields:
            if field not in vendor:
                errors.append(f"Vendor {i}: Missing required field '{field}'")
    
    if errors:
        print(f"  ❌ Found {len(errors)} errors:")
        for error in errors:
            print(f"    - {error}")
        return False
    else:
        print(f"  ✓ All {len(SAMPLE_VENDORS)} vendors are valid")
        return True


def validate_users():
    """Validate user data structure."""
    print("Validating users...")
    errors = []
    
    emails = set()
    valid_roles = ["admin", "manager", "user"]
    
    for i, user in enumerate(SAMPLE_USERS):
        # Check required fields
        required_fields = ["email", "password", "full_name", "role"]
        for field in required_fields:
            if field not in user:
                errors.append(f"User {i}: Missing required field '{field}'")
        
        # Check for duplicate emails
        if "email" in user:
            if user["email"] in emails:
                errors.append(f"User {i}: Duplicate email '{user['email']}'")
            emails.add(user["email"])
        
        # Check role is valid
        if "role" in user and user["role"] not in valid_roles:
            errors.append(f"User {i}: Invalid role '{user['role']}'. Must be one of {valid_roles}")
    
    if errors:
        print(f"  ❌ Found {len(errors)} errors:")
        for error in errors:
            print(f"    - {error}")
        return False
    else:
        print(f"  ✓ All {len(SAMPLE_USERS)} users are valid")
        return True


def main():
    """Run all validations."""
    print("\n" + "="*60)
    print("Seed Data Validation")
    print("="*60 + "\n")
    
    results = []
    results.append(validate_products())
    results.append(validate_vendors())
    results.append(validate_users())
    
    print("\n" + "="*60)
    if all(results):
        print("✓ All validations passed!")
        print("="*60 + "\n")
        return 0
    else:
        print("❌ Some validations failed!")
        print("="*60 + "\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
