import api from './api';

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

export const inventoryService = {
  /**
   * Adjust stock level for a product
   */
  async adjustStock(data: StockAdjustment): Promise<InventoryTransaction> {
    const response = await api.post<InventoryTransaction>('/inventory/adjust', data);
    return response.data;
  },

  /**
   * Get stock movements/history
   */
  async getMovements(productId?: string): Promise<InventoryTransaction[]> {
    const params = productId ? `?product_id=${productId}` : '';
    const response = await api.get<InventoryTransaction[]>(`/inventory/movements${params}`);
    return response.data;
  },

  /**
   * Get stock movement history for a specific product
   */
  async getProductHistory(productId: string): Promise<InventoryTransaction[]> {
    const response = await api.get<InventoryTransaction[]>(`/inventory/products/${productId}/history`);
    return response.data;
  },
};
