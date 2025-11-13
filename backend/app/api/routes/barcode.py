"""API routes for barcode scanning and lookup."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.barcode import (
    BarcodeScanRequest,
    BarcodeScanResponse,
    BarcodeLinkRequest,
    BarcodeLinkResponse,
    BarcodeProductInfo
)
from app.services.barcode_service import BarcodeService

router = APIRouter(prefix="/barcode", tags=["barcode"])


@router.post("/scan", response_model=BarcodeScanResponse, status_code=status.HTTP_200_OK)
async def scan_barcode(
    request: BarcodeScanRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Process a scanned barcode.
    
    This endpoint checks if the barcode exists in the database. If found, it returns
    the product information. If not found, it attempts to fetch product information
    from an external barcode API.
    
    Args:
        request: Barcode scan request with barcode value
        db: Database session
        current_user: Authenticated user
        
    Returns:
        BarcodeScanResponse with product info or external data
    """
    barcode_service = BarcodeService(db)
    
    # First, check if barcode exists in database
    product = barcode_service.lookup_barcode(request.barcode)
    
    if product:
        # Product found in database
        return BarcodeScanResponse(
            found=True,
            product_id=product.id,
            product_name=product.name,
            current_stock=product.current_stock,
            external_info=None
        )
    else:
        # Product not found, try external API
        external_info = await barcode_service.fetch_external_product_info(request.barcode)
        
        return BarcodeScanResponse(
            found=False,
            product_id=None,
            product_name=None,
            current_stock=None,
            external_info=external_info
        )


@router.get("/lookup/{code}", response_model=BarcodeScanResponse, status_code=status.HTTP_200_OK)
async def lookup_barcode(
    code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Look up a product by barcode code.
    
    Similar to scan endpoint but uses path parameter for the barcode.
    Checks database first, then falls back to external API if not found.
    
    Args:
        code: Barcode value
        db: Database session
        current_user: Authenticated user
        
    Returns:
        BarcodeScanResponse with product info or external data
    """
    barcode_service = BarcodeService(db)
    
    # Check if barcode exists in database
    product = barcode_service.lookup_barcode(code)
    
    if product:
        # Product found in database
        return BarcodeScanResponse(
            found=True,
            product_id=product.id,
            product_name=product.name,
            current_stock=product.current_stock,
            external_info=None
        )
    else:
        # Product not found, try external API
        external_info = await barcode_service.fetch_external_product_info(code)
        
        return BarcodeScanResponse(
            found=False,
            product_id=None,
            product_name=None,
            current_stock=None,
            external_info=external_info
        )


@router.post("/link", response_model=BarcodeLinkResponse, status_code=status.HTTP_200_OK)
def link_barcode(
    request: BarcodeLinkRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Link a barcode to an existing product.
    
    This endpoint allows associating a barcode with a product that doesn't have one yet,
    or updating an existing barcode association.
    
    Args:
        request: Barcode link request with barcode and product_id
        db: Database session
        current_user: Authenticated user
        
    Returns:
        BarcodeLinkResponse with success status and message
    """
    barcode_service = BarcodeService(db)
    
    # Link the barcode to the product
    product = barcode_service.link_barcode_to_product(request.barcode, request.product_id)
    
    return BarcodeLinkResponse(
        success=True,
        message=f"Barcode '{request.barcode}' successfully linked to product '{product.name}'",
        product_id=product.id
    )
