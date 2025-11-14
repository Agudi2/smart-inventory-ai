import api from './api';

export interface DashboardMetrics {
  total_products: number;
  low_stock_count: number;
  active_alerts: number;
  total_vendors: number;
}

export const metricsService = {
  getDashboardMetrics: async (): Promise<DashboardMetrics> => {
    try {
      const response = await api.get('/metrics');
      const data = response.data;
      
      // Extract metrics from the backend response structure
      return {
        total_products: data.database?.products || 0,
        low_stock_count: 0, // Will be calculated from products with low stock
        active_alerts: data.database?.active_alerts || 0,
        total_vendors: data.database?.vendors || 0,
      };
    } catch (error) {
      // Return default values if metrics endpoint doesn't exist yet
      return {
        total_products: 0,
        low_stock_count: 0,
        active_alerts: 0,
        total_vendors: 0,
      };
    }
  },
};
