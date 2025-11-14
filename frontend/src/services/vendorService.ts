import api from './api';

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

export const vendorService = {
  /**
   * Get all vendors
   */
  async getAllVendors(skip = 0, limit = 100): Promise<Vendor[]> {
    const response = await api.get<Vendor[]>('/vendors', {
      params: { skip, limit },
    });
    return response.data;
  },

  /**
   * Get a specific vendor by ID
   */
  async getVendor(vendorId: string): Promise<Vendor> {
    const response = await api.get<Vendor>(`/vendors/${vendorId}`);
    return response.data;
  },

  /**
   * Create a new vendor
   */
  async createVendor(data: VendorCreate): Promise<Vendor> {
    const response = await api.post<Vendor>('/vendors', data);
    return response.data;
  },

  /**
   * Update a vendor
   */
  async updateVendor(vendorId: string, data: VendorUpdate): Promise<Vendor> {
    const response = await api.put<Vendor>(`/vendors/${vendorId}`, data);
    return response.data;
  },

  /**
   * Delete a vendor
   */
  async deleteVendor(vendorId: string): Promise<void> {
    await api.delete(`/vendors/${vendorId}`);
  },

  /**
   * Get all vendors for a specific product with price comparison
   */
  async getProductVendors(productId: string): Promise<VendorPrice[]> {
    const response = await api.get<VendorPrice[]>(`/products/${productId}/vendors`);
    return response.data;
  },

  /**
   * Add or update a vendor price for a product
   */
  async addVendorPrice(vendorId: string, data: VendorPriceCreate): Promise<VendorPrice> {
    const response = await api.post<VendorPrice>(`/vendors/${vendorId}/prices`, data);
    return response.data;
  },

  /**
   * Update a vendor price
   */
  async updateVendorPrice(
    vendorId: string,
    productId: string,
    data: VendorPriceUpdate
  ): Promise<VendorPrice> {
    const response = await api.put<VendorPrice>(
      `/vendors/${vendorId}/prices/${productId}`,
      data
    );
    return response.data;
  },
};
