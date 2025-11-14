// Common types for the application
export interface User {
  id: number;
  email: string;
  full_name: string;
  role: 'admin' | 'manager' | 'staff';
  is_active: boolean;
  created_at: string;
}

export interface Product {
  id: number;
  name: string;
  sku: string;
  description?: string;
  category: string;
  unit_price: number;
  reorder_point: number;
  reorder_quantity: number;
  barcode?: string;
  created_at: string;
  updated_at: string;
}

export interface InventoryItem {
  id: number;
  product_id: number;
  quantity: number;
  location: string;
  last_updated: string;
  product?: Product;
}

export interface Vendor {
  id: number;
  name: string;
  contact_person?: string;
  email?: string;
  phone?: string;
  address?: string;
  created_at: string;
}

export interface Alert {
  id: number;
  product_id: number;
  alert_type: 'low_stock' | 'overstock' | 'expiring_soon' | 'demand_spike';
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  is_resolved: boolean;
  created_at: string;
  resolved_at?: string;
  product?: Product;
}

export interface Prediction {
  product_id: number;
  predicted_demand: number;
  confidence_score: number;
  prediction_date: string;
  factors?: Record<string, any>;
}

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
