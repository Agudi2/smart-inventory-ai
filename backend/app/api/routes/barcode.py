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


@router.post(
    "/scan",
    response_model=BarcodeScanResponse,
    status_code=status.HTTP_200_OK,
    summary="Scan a barcode",
    description="Process a scanned barcode and return product information from database or external API.",
    responses={
        200: {
            "description": "Barcode processed successfully",
            "content": {
                "application/json": {
                    "examples": {
                        "found_in_database": {
                            "summary": "Product found in database",
                            "value": {
                                "found": True,
                                "product_id": "123e4567-e89b-12d3-a456-426614174001",
                                "product_name": "Widget A",
                                "current_stock": 150,
                                "external_info": None
                            }
                        },
                        "found_externally": {
                            "summary": "Product found via external API",
                            "value": {
                                "found": False,
                                "product_id": None,
                                "product_name": None,
                                "current_stock": None,
                                "external_info": {
                                    "barcode": "012345678905",
                                    "product_name": "Example Product",
                                    "category": "Electronics",
                                    "manufacturer": "Example Corp"
                                }
                            }
                        }
                    }
                }
            }
        },
        401: {"description": "Not authenticated"}
    }
)
async def scan_barcode(
    request: BarcodeScanRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Process a scanned barcode and retrieve product information.
    
    This endpoint implements a two-tier lookup strategy:
    1. First checks if the barcode exists in the local database
    2. If not found locally, queries external barcode APIs for product information
    
    **Request Body:**
    - **barcode**: The scanned barcode value (UPC, EAN, etc.)
    
    **Response Scenarios:**
    
    **Found in Database:**
    - Returns `found: true` with complete product information
    - Includes product_id, name, and current stock level
    - Ready for immediate stock adjustment
    
    **Found Externally:**
    - Returns `found: false` with external product information
    - Includes suggested product name, category, and manufacturer
    - Can be used to create a new product in the system
    
    **Not Found:**
    - Returns `found: false` with null external_info
    - Indicates barcode is not recognized by any source
    
    **Use Cases:**
    - Webcam-based barcode scanning for stock updates
    - Quick product lookup during receiving
    - New product discovery and onboarding
    
    **Example Request:**
    ```json
    {
        "barcode": "012345678905"
    }
    ```
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


@router.get(
    "/lookup/{code}",
    response_model=BarcodeScanResponse,
    status_code=status.HTTP_200_OK,
    summary="Lookup product by barcode",
    description="Look up a product using its barcode value. Checks local database first, then external APIs.",
    responses={
        200: {
            "description": "Barcode lookup completed",
            "content": {
                "application/json": {
                    "example": {
                        "found": True,
                        "product_id": "123e4567-e89b-12d3-a456-426614174001",
                        "product_name": "Widget A",
                        "current_stock": 150,
                        "external_info": None
                    }
                }
            }
        },
        401: {"description": "Not authenticated"}
    }
)
async def lookup_barcode(
    code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Look up a product by barcode code using GET request.
    
    This endpoint provides the same functionality as POST /scan but uses
    a GET request with the barcode as a path parameter. Useful for:
    - Direct URL-based lookups
    - Browser-based testing
    - Integration with barcode scanner hardware that sends GET requests
    
    **Path Parameters:**
    - **code**: The barcode value to look up (UPC, EAN, etc.)
    
    **Lookup Process:**
    1. Searches local product database for matching barcode
    2. If found, returns product details immediately
    3. If not found, queries external barcode APIs
    4. Returns external product information if available
    
    **Returns:**
    - Same response format as POST /scan endpoint
    - `found: true` if product exists in database
    - `found: false` with external_info if found via external API
    - `found: false` with null external_info if not found anywhere
    
    **Example:**
    ```
    GET /api/v1/barcode/lookup/012345678905
    ```
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


@router.post(
    "/link",
    response_model=BarcodeLinkResponse,
    status_code=status.HTTP_200_OK,
    summary="Link barcode to product",
    description="Associate a barcode with an existing product in the database.",
    responses={
        200: {
            "description": "Barcode linked successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Barcode '012345678905' successfully linked to product 'Widget A'",
                        "product_id": "123e4567-e89b-12d3-a456-426614174001"
                    }
                }
            }
        },
        400: {"description": "Barcode already in use or invalid request"},
        401: {"description": "Not authenticated"},
        404: {"description": "Product not found"}
    }
)
def link_barcode(
    request: BarcodeLinkRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Link a barcode to an existing product.
    
    This endpoint allows you to associate a barcode with a product that doesn't
    have one yet, or update an existing barcode association. Useful when:
    - Adding barcodes to manually created products
    - Updating incorrect barcode associations
    - Linking products discovered via external barcode APIs
    
    **Request Body:**
    - **barcode**: The barcode value to link (must be unique)
    - **product_id**: UUID of the product to link the barcode to
    
    **Validation:**
    - Product must exist in the database
    - Barcode must be unique (not already assigned to another product)
    - Barcode cannot be empty or null
    
    **Returns:**
    - Success confirmation with product details
    - Updated product_id for verification
    
    **Use Cases:**
    - After scanning an unknown barcode and creating a new product
    - Correcting barcode associations
    - Bulk barcode assignment workflows
    
    **Example Request:**
    ```json
    {
        "barcode": "012345678905",
        "product_id": "123e4567-e89b-12d3-a456-426614174001"
    }
    ```
    """
    barcode_service = BarcodeService(db)
    
    # Link the barcode to the product
    product = barcode_service.link_barcode_to_product(request.barcode, request.product_id)
    
    return BarcodeLinkResponse(
        success=True,
        message=f"Barcode '{request.barcode}' successfully linked to product '{product.name}'",
        product_id=product.id
    )
