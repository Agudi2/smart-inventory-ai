// Common types for the application

// ============= Auth Types =============
export interface User {
  id: string;
  email: string;
  full_name?: string;
  role: 'admin' | 'manager' | 'user';
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name?: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

// ============= Product Types =============
export interface Product {
  id: string;
  sku: string;
  name: string;
  category: string;
  current_stock: number;
  reorder_threshold: number;
  stock_status: 'sufficient' | 'low' | 'critical';
  barcode?: string;
  unit_cost?: number;
  predicted_depletion_date?: string;
  created_at: string;
  updated_at: string;
}

export interface ProductCreate {
  sku: string;
  name: string;
  category: string;
  current_stock: number;
  reorder_threshold: number;
  barcode?: string;
  unit_cost?: number;
}

export interface ProductUpdate {
  name?: string;
  category?: string;
  current_stock?: number;
  reorder_threshold?: number;
  barcode?: string;
  unit_cost?: number;
}

export interface ProductFilters {
  category?: string;
  search?: string;
  skip?: number;
  limit?: number;
}

// ============= Inventory Types =============
export interface StockAdjustment {
  product_id: string;
  quantity: number;
  reason?: string;
}

export interface InventoryTransaction {
  id: string;
  product_id: string;
  transaction_type: string;
  quantity: number;
  previous_stock: number;
  new_stock: number;
  reason?: string;
  user_id?: string;
  created_at: string;
}

// ============= Barcode Types =============
export interface BarcodeProductInfo {
  barcode: string;
  title?: string;
  brand?: string;
  category?: string;
  description?: string;
  images?: string[];
}

export interface BarcodeScanResponse {
  found: boolean;
  product_id?: string;
  product_name?: string;
  current_stock?: number;
  external_info?: BarcodeProductInfo;
}

export interface BarcodeLinkRequest {
  barcode: string;
  product_id: string;
}

export interface BarcodeLinkResponse {
  success: boolean;
  message: string;
  product_id: string;
}

// ============= Prediction Types =============
export interface ForecastPoint {
  date: string;
  predicted_stock: number;
  lower_bound?: number;
  upper_bound?: number;
}

export interface PredictionResult {
  product_id: string;
  product_name?: string;
  product_sku?: string;
  current_stock?: number;
  predicted_depletion_date?: string;
  confidence_score?: number;
  daily_consumption_rate?: number;
  model_version?: string;
  model_type?: string;
  forecast?: ForecastPoint[];
  created_at?: string;
}

export interface TrainModelRequest {
  product_id?: string;
  force_retrain?: boolean;
}

export interface TrainModelResponse {
  success: boolean;
  message: string;
  product_id?: string;
  model_metrics?: Record<string, any>;
}

// ============= Vendor Types =============
export interface Vendor {
  id: string;
  name: string;
  contact_email?: string;
  contact_phone?: string;
  address?: string;
  created_at: string;
  updated_at: string;
  product_count?: number;
}

export interface VendorCreate {
  name: string;
  contact_email?: string;
  contact_phone?: string;
  address?: string;
}

export interface VendorUpdate {
  name?: string;
  contact_email?: string;
  contact_phone?: string;
  address?: string;
}

export interface VendorPrice {
  id: string;
  vendor_id: string;
  product_id: string;
  unit_price: number;
  lead_time_days: number;
  minimum_order_quantity: number;
  last_updated: string;
  is_recommended: boolean;
  vendor_name?: string;
  vendor_email?: string;
  vendor_phone?: string;
}

export interface VendorPriceCreate {
  product_id: string;
  unit_price: number;
  lead_time_days?: number;
  minimum_order_quantity?: number;
}

export interface VendorPriceUpdate {
  unit_price?: number;
  lead_time_days?: number;
  minimum_order_quantity?: number;
}

// ============= Alert Types =============
export interface Alert {
  id: string;
  product_id: string;
  alert_type: 'low_stock' | 'predicted_depletion';
  severity: 'warning' | 'critical';
  message: string;
  status: 'active' | 'acknowledged' | 'resolved';
  created_at: string;
  acknowledged_at?: string;
  resolved_at?: string;
  product_name?: string;
  product_sku?: string;
  current_stock?: number;
}

export interface AlertSettings {
  alert_threshold_days: number;
  low_stock_enabled: boolean;
  predicted_depletion_enabled: boolean;
}

// ============= Common Types =============
export interface ApiError {
  detail: string;
  status_code?: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}
