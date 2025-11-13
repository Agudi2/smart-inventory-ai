from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.models.vendor import Vendor
from app.models.vendor_price import VendorPrice
from app.models.product import Product
from app.schemas.vendor import (
    VendorCreate,
    VendorUpdate,
    VendorPriceCreate,
    VendorPriceUpdate,
    ProductVendorResponse
)
from app.core.exceptions import NotFoundException, ValidationException


class VendorService:
    """Service for managing vendors and vendor prices."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_all_vendors(self, skip: int = 0, limit: int = 100) -> List[Vendor]:
        """
        Get all vendors with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of vendors
        """
        return self.db.query(Vendor).offset(skip).limit(limit).all()
    
    def get_vendor_by_id(self, vendor_id: UUID) -> Vendor:
        """
        Get vendor by ID.
        
        Args:
            vendor_id: Vendor UUID
            
        Returns:
            Vendor object
            
        Raises:
            NotFoundException: If vendor not found
        """
        vendor = self.db.query(Vendor).filter(Vendor.id == vendor_id).first()
        if not vendor:
            raise NotFoundException(f"Vendor with id {vendor_id} not found")
        return vendor
    
    def create_vendor(self, vendor_data: VendorCreate) -> Vendor:
        """
        Create a new vendor.
        
        Args:
            vendor_data: Vendor creation data
            
        Returns:
            Created vendor
        """
        vendor = Vendor(**vendor_data.model_dump())
        self.db.add(vendor)
        self.db.commit()
        self.db.refresh(vendor)
        return vendor
    
    def update_vendor(self, vendor_id: UUID, vendor_data: VendorUpdate) -> Vendor:
        """
        Update vendor information.
        
        Args:
            vendor_id: Vendor UUID
            vendor_data: Updated vendor data
            
        Returns:
            Updated vendor
            
        Raises:
            NotFoundException: If vendor not found
        """
        vendor = self.get_vendor_by_id(vendor_id)
        
        update_data = vendor_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(vendor, field, value)
        
        vendor.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(vendor)
        return vendor
    
    def delete_vendor(self, vendor_id: UUID) -> bool:
        """
        Delete a vendor.
        
        Args:
            vendor_id: Vendor UUID
            
        Returns:
            True if deleted successfully
            
        Raises:
            NotFoundException: If vendor not found
        """
        vendor = self.get_vendor_by_id(vendor_id)
        self.db.delete(vendor)
        self.db.commit()
        return True
    
    def get_vendors_for_product(self, product_id: UUID) -> List[ProductVendorResponse]:
        """
        Get all vendors for a specific product with price comparison.
        
        Args:
            product_id: Product UUID
            
        Returns:
            List of vendors with pricing information, sorted by price
            
        Raises:
            NotFoundException: If product not found
        """
        # Verify product exists
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise NotFoundException(f"Product with id {product_id} not found")
        
        # Get all vendor prices for this product
        vendor_prices = (
            self.db.query(VendorPrice, Vendor)
            .join(Vendor, VendorPrice.vendor_id == Vendor.id)
            .filter(VendorPrice.product_id == product_id)
            .order_by(VendorPrice.unit_price.asc())
            .all()
        )
        
        if not vendor_prices:
            return []
        
        # Find the lowest price for recommendation
        lowest_price = vendor_prices[0][0].unit_price if vendor_prices else None
        
        # Build response with vendor information
        result = []
        for vendor_price, vendor in vendor_prices:
            is_recommended = (vendor_price.unit_price == lowest_price)
            
            result.append(ProductVendorResponse(
                id=vendor_price.id,
                vendor_id=vendor_price.vendor_id,
                product_id=vendor_price.product_id,
                unit_price=vendor_price.unit_price,
                lead_time_days=vendor_price.lead_time_days,
                minimum_order_quantity=vendor_price.minimum_order_quantity,
                last_updated=vendor_price.last_updated,
                is_recommended=is_recommended,
                vendor_name=vendor.name,
                vendor_email=vendor.contact_email,
                vendor_phone=vendor.contact_phone
            ))
        
        return result
    
    def add_vendor_price(self, vendor_id: UUID, price_data: VendorPriceCreate) -> VendorPrice:
        """
        Add or update a vendor price for a product.
        
        Args:
            vendor_id: Vendor UUID
            price_data: Vendor price data
            
        Returns:
            Created or updated vendor price
            
        Raises:
            NotFoundException: If vendor or product not found
        """
        # Verify vendor exists
        vendor = self.get_vendor_by_id(vendor_id)
        
        # Verify product exists
        product = self.db.query(Product).filter(Product.id == price_data.product_id).first()
        if not product:
            raise NotFoundException(f"Product with id {price_data.product_id} not found")
        
        # Check if price already exists for this vendor-product combination
        existing_price = (
            self.db.query(VendorPrice)
            .filter(
                VendorPrice.vendor_id == vendor_id,
                VendorPrice.product_id == price_data.product_id
            )
            .first()
        )
        
        if existing_price:
            # Update existing price
            existing_price.unit_price = price_data.unit_price
            existing_price.lead_time_days = price_data.lead_time_days
            existing_price.minimum_order_quantity = price_data.minimum_order_quantity
            existing_price.last_updated = datetime.utcnow()
            self.db.commit()
            self.db.refresh(existing_price)
            return existing_price
        else:
            # Create new price
            vendor_price = VendorPrice(
                vendor_id=vendor_id,
                **price_data.model_dump()
            )
            self.db.add(vendor_price)
            self.db.commit()
            self.db.refresh(vendor_price)
            return vendor_price
    
    def update_vendor_price(
        self,
        vendor_id: UUID,
        product_id: UUID,
        price_data: VendorPriceUpdate
    ) -> VendorPrice:
        """
        Update an existing vendor price.
        
        Args:
            vendor_id: Vendor UUID
            product_id: Product UUID
            price_data: Updated price data
            
        Returns:
            Updated vendor price
            
        Raises:
            NotFoundException: If vendor price not found
        """
        vendor_price = (
            self.db.query(VendorPrice)
            .filter(
                VendorPrice.vendor_id == vendor_id,
                VendorPrice.product_id == product_id
            )
            .first()
        )
        
        if not vendor_price:
            raise NotFoundException(
                f"Vendor price not found for vendor {vendor_id} and product {product_id}"
            )
        
        update_data = price_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(vendor_price, field, value)
        
        vendor_price.last_updated = datetime.utcnow()
        self.db.commit()
        self.db.refresh(vendor_price)
        return vendor_price
    
    def get_recommended_vendor(self, product_id: UUID) -> Optional[ProductVendorResponse]:
        """
        Get the recommended vendor (lowest price) for a product.
        
        Args:
            product_id: Product UUID
            
        Returns:
            Recommended vendor with pricing info, or None if no vendors
        """
        vendors = self.get_vendors_for_product(product_id)
        if not vendors:
            return None
        
        # The list is already sorted by price, so first item is recommended
        return vendors[0]
    
    def get_vendor_product_count(self, vendor_id: UUID) -> int:
        """
        Get the number of products associated with a vendor.
        
        Args:
            vendor_id: Vendor UUID
            
        Returns:
            Count of products
        """
        count = (
            self.db.query(func.count(VendorPrice.id))
            .filter(VendorPrice.vendor_id == vendor_id)
            .scalar()
        )
        return count or 0
