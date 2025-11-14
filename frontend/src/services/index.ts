// Export all API services
export { api } from './api';
export { authService } from './authService';
export { productService } from './productService';
export { inventoryService } from './inventoryService';
export { barcodeService } from './barcodeService';
export { predictionService } from './predictionService';
export { vendorService } from './vendorService';
export { alertService } from './alertService';

// Re-export types from services
export type { Product, ProductCreate, ProductUpdate, ProductFilters } from './productService';
export type { StockAdjustment, InventoryTransaction } from './inventoryService';
export type { 
  BarcodeProductInfo, 
  BarcodeScanResponse, 
  BarcodeLinkRequest,
  BarcodeLinkResponse 
} from './barcodeService';
export type { ForecastPoint, PredictionResult } from './predictionService';
export type { 
  Vendor, 
  VendorCreate, 
  VendorUpdate, 
  VendorPrice,
  VendorPriceCreate,
  VendorPriceUpdate 
} from './vendorService';
export type { Alert, AlertSettings } from './alertService';
