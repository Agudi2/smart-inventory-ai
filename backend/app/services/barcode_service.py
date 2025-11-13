"""Barcode service for barcode lookup and external API integration."""

import logging
from typing import Optional
from uuid import UUID

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import BarcodeNotFoundException, ValidationException
from app.models.product import Product
from app.schemas.barcode import BarcodeProductInfo

logger = logging.getLogger(__name__)


class BarcodeService:
    """Service class for barcode-related operations."""
    
    def __init__(self, db: Session):
        """Initialize the barcode service with a database session."""
        self.db = db
    
    def lookup_barcode(self, barcode: str) -> Optional[Product]:
        """
        Look up a product by barcode in the database.
        
        Args:
            barcode: Barcode string to search for
            
        Returns:
            Product object if found, None otherwise
        """
        return self.db.query(Product).filter(Product.barcode == barcode).first()
    
    async def fetch_external_product_info(self, barcode: str) -> Optional[BarcodeProductInfo]:
        """
        Fetch product information from external barcode API.
        
        Uses UPC Item DB API as the external source. Falls back gracefully if API is unavailable.
        
        Args:
            barcode: Barcode string to look up
            
        Returns:
            BarcodeProductInfo object if found, None if not found or API unavailable
        """
        # If no API key is configured, return None
        if not settings.barcode_api_key:
            logger.warning("Barcode API key not configured, skipping external lookup")
            return None
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # UPC Item DB API format
                response = await client.get(
                    settings.barcode_api_url,
                    params={"upc": barcode},
                    headers={"user_key": settings.barcode_api_key} if settings.barcode_api_key else {}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Parse UPC Item DB response format
                    if data.get("code") == "OK" and data.get("items"):
                        item = data["items"][0]
                        
                        return BarcodeProductInfo(
                            barcode=barcode,
                            title=item.get("title"),
                            brand=item.get("brand"),
                            category=item.get("category"),
                            description=item.get("description"),
                            images=item.get("images", [])
                        )
                    else:
                        logger.info(f"Barcode {barcode} not found in external API")
                        return None
                else:
                    logger.warning(f"External API returned status {response.status_code}")
                    return None
                    
        except httpx.TimeoutException:
            logger.warning(f"Timeout while fetching external product info for barcode {barcode}")
            return None
        except Exception as e:
            logger.error(f"Error fetching external product info: {str(e)}")
            return None
    
    def link_barcode_to_product(self, barcode: str, product_id: UUID) -> Product:
        """
        Link a barcode to an existing product.
        
        Args:
            barcode: Barcode string to link
            product_id: UUID of the product to link to
            
        Returns:
            Updated Product object
            
        Raises:
            ValidationException: If barcode already exists for another product
            BarcodeNotFoundException: If product not found
        """
        # Check if barcode already exists for another product
        existing_product = self.lookup_barcode(barcode)
        if existing_product and existing_product.id != product_id:
            raise ValidationException(
                f"Barcode '{barcode}' is already linked to product '{existing_product.name}'"
            )
        
        # Get the product to link to
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise BarcodeNotFoundException(f"Product with ID {product_id} not found")
        
        # Update the product's barcode
        product.barcode = barcode
        self.db.commit()
        self.db.refresh(product)
        
        return product
    
    def get_product_by_barcode(self, barcode: str) -> Product:
        """
        Get a product by barcode, raising an exception if not found.
        
        Args:
            barcode: Barcode string to search for
            
        Returns:
            Product object
            
        Raises:
            BarcodeNotFoundException: If barcode is not found
        """
        product = self.lookup_barcode(barcode)
        if not product:
            raise BarcodeNotFoundException(f"No product found with barcode '{barcode}'")
        return product
