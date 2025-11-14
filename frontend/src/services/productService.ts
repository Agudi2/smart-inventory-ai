import api from './api';

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

export const productService = {
  /**
   * Get all products with optional filters
   */
  async getProducts(filters?: ProductFilters): Promise<Product[]> {
    const params = new URLSearchParams();
    
    if (filters?.category) {
      params.append('category', filters.category);
    }
    if (filters?.search) {
      params.append('search', filters.search);
    }
    if (filters?.skip !== undefined) {
      params.append('skip', filters.skip.toString());
    }
    if (filters?.limit !== undefined) {
      params.append('limit', filters.limit.toString());
    }

    const response = await api.get<Product[]>(`/products?${params.toString()}`);
    return response.data;
  },

  /**
   * Get a single product by ID
   */
  async getProduct(id: string): Promise<Product> {
    const response = await api.get<Product>(`/products/${id}`);
    return response.data;
  },

  /**
   * Create a new product
   */
  async createProduct(data: ProductCreate): Promise<Product> {
    const response = await api.post<Product>('/products', data);
    return response.data;
  },

  /**
   * Update an existing product
   */
  async updateProduct(id: string, data: ProductUpdate): Promise<Product> {
    const response = await api.put<Product>(`/products/${id}`, data);
    return response.data;
  },

  /**
   * Delete a product
   */
  async deleteProduct(id: string): Promise<void> {
    await api.delete(`/products/${id}`);
  },
};
