"""Product service for business logic and CRUD operations."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.exceptions import ProductNotFoundException, ValidationException
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate


class ProductService:
    """Service class for product-related operations."""
    
    def __init__(self, db: Session):
        """Initialize the product service with a database session."""
        self.db = db
    
    def get_all_products(
        self,
        category: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Product]:
        """
        Retrieve all products with optional filtering.
        
        Args:
            category: Filter by category
            search: Search in name, SKU, or category
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return
            
        Returns:
            List of Product objects
        """
        query = self.db.query(Product)
        
        # Apply category filter
        if category:
            query = query.filter(Product.category == category)
        
        # Apply search filter
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Product.name.ilike(search_term),
                    Product.sku.ilike(search_term),
                    Product.category.ilike(search_term)
                )
            )
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        return query.all()
    
    def get_product_by_id(self, product_id: UUID) -> Product:
        """
        Retrieve a product by its ID.
        
        Args:
            product_id: UUID of the product
            
        Returns:
            Product object
            
        Raises:
            ProductNotFoundException: If product is not found
        """
        product = self.db.query(Product).filter(Product.id == product_id).first()
        
        if not product:
            raise ProductNotFoundException(f"Product with ID {product_id} not found")
        
        return product
    
    def get_product_by_sku(self, sku: str) -> Optional[Product]:
        """
        Retrieve a product by its SKU.
        
        Args:
            sku: Stock Keeping Unit
            
        Returns:
            Product object or None if not found
        """
        return self.db.query(Product).filter(Product.sku == sku).first()
    
    def create_product(self, product_data: ProductCreate) -> Product:
        """
        Create a new product.
        
        Args:
            product_data: Product creation data
            
        Returns:
            Created Product object
            
        Raises:
            ValidationException: If SKU or barcode already exists
        """
        # Check if SKU already exists
        existing_product = self.get_product_by_sku(product_data.sku)
        if existing_product:
            raise ValidationException(f"Product with SKU '{product_data.sku}' already exists")
        
        # Check if barcode already exists (if provided)
        if product_data.barcode:
            existing_barcode = self.db.query(Product).filter(
                Product.barcode == product_data.barcode
            ).first()
            if existing_barcode:
                raise ValidationException(f"Product with barcode '{product_data.barcode}' already exists")
        
        # Create new product
        product = Product(**product_data.model_dump())
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        
        return product
    
    def update_product(self, product_id: UUID, product_data: ProductUpdate) -> Product:
        """
        Update an existing product.
        
        Args:
            product_id: UUID of the product to update
            product_data: Product update data
            
        Returns:
            Updated Product object
            
        Raises:
            ProductNotFoundException: If product is not found
            ValidationException: If barcode already exists for another product
        """
        product = self.get_product_by_id(product_id)
        
        # Check if barcode is being updated and already exists for another product
        if product_data.barcode is not None:
            existing_barcode = self.db.query(Product).filter(
                Product.barcode == product_data.barcode,
                Product.id != product_id
            ).first()
            if existing_barcode:
                raise ValidationException(f"Product with barcode '{product_data.barcode}' already exists")
        
        # Update product fields
        update_data = product_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(product, field, value)
        
        self.db.commit()
        self.db.refresh(product)
        
        return product
    
    def delete_product(self, product_id: UUID) -> bool:
        """
        Delete a product.
        
        Args:
            product_id: UUID of the product to delete
            
        Returns:
            True if deletion was successful
            
        Raises:
            ProductNotFoundException: If product is not found
        """
        product = self.get_product_by_id(product_id)
        
        self.db.delete(product)
        self.db.commit()
        
        return True
    
    def calculate_stock_status(self, product: Product) -> str:
        """
        Calculate stock status based on current stock and reorder threshold.
        
        Status logic:
        - critical: current_stock == 0
        - low: 0 < current_stock <= reorder_threshold
        - sufficient: current_stock > reorder_threshold
        
        Args:
            product: Product object
            
        Returns:
            Stock status string: 'sufficient', 'low', or 'critical'
        """
        if product.current_stock == 0:
            return "critical"
        elif product.current_stock <= product.reorder_threshold:
            return "low"
        else:
            return "sufficient"
