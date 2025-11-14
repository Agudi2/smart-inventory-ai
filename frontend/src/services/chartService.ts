import api from './api';

export interface StockLevelData {
  status: string;
  count: number;
  color: string;
}

export interface ConsumptionTrendData {
  date: string;
  additions: number;
  removals: number;
  net: number;
}

export interface CategoryDistributionData {
  category: string;
  count: number;
  value: number;
  [key: string]: string | number;
}

export interface AlertTrendData {
  date: string;
  low_stock: number;
  predicted_depletion: number;
  total: number;
}

export const chartService = {
  /**
   * Get stock level overview data grouped by status
   */
  getStockLevelOverview: async (): Promise<StockLevelData[]> => {
    try {
      const response = await api.get('/products');
      const products = response.data;
      
      // Group products by stock status
      const statusCounts = products.reduce((acc: any, product: any) => {
        const status = product.stock_status || 'sufficient';
        acc[status] = (acc[status] || 0) + 1;
        return acc;
      }, {});
      
      // Map to chart data with colors
      const statusColors: Record<string, string> = {
        sufficient: '#10b981', // green
        low: '#f59e0b',        // yellow
        critical: '#ef4444',   // red
      };
      
      return Object.entries(statusCounts).map(([status, count]) => ({
        status: status.charAt(0).toUpperCase() + status.slice(1),
        count: count as number,
        color: statusColors[status] || '#6b7280',
      }));
    } catch (error) {
      console.error('Error fetching stock level overview:', error);
      return [];
    }
  },

  /**
   * Get consumption trend data from inventory movements
   */
  getConsumptionTrend: async (days: number = 30): Promise<ConsumptionTrendData[]> => {
    try {
      const response = await api.get('/inventory/movements', {
        params: { limit: 1000 }
      });
      const movements = response.data;
      
      // Group movements by date
      const dateMap = new Map<string, { additions: number; removals: number }>();
      
      movements.forEach((movement: any) => {
        const date = new Date(movement.created_at).toISOString().split('T')[0];
        const existing = dateMap.get(date) || { additions: 0, removals: 0 };
        
        if (movement.quantity > 0) {
          existing.additions += movement.quantity;
        } else {
          existing.removals += Math.abs(movement.quantity);
        }
        
        dateMap.set(date, existing);
      });
      
      // Convert to array and sort by date
      const trendData = Array.from(dateMap.entries())
        .map(([date, data]) => ({
          date,
          additions: data.additions,
          removals: data.removals,
          net: data.additions - data.removals,
        }))
        .sort((a, b) => a.date.localeCompare(b.date))
        .slice(-days); // Get last N days
      
      return trendData;
    } catch (error) {
      console.error('Error fetching consumption trend:', error);
      return [];
    }
  },

  /**
   * Get category distribution data
   */
  getCategoryDistribution: async (): Promise<CategoryDistributionData[]> => {
    try {
      const response = await api.get('/products');
      const products = response.data;
      
      // Group products by category
      const categoryMap = new Map<string, number>();
      
      products.forEach((product: any) => {
        const category = product.category || 'Uncategorized';
        categoryMap.set(category, (categoryMap.get(category) || 0) + 1);
      });
      
      // Convert to array
      return Array.from(categoryMap.entries())
        .map(([category, count]) => ({
          category,
          count,
          value: count, // For pie chart
        }))
        .sort((a, b) => b.count - a.count);
    } catch (error) {
      console.error('Error fetching category distribution:', error);
      return [];
    }
  },

  /**
   * Get alert frequency trend data
   */
  getAlertTrend: async (days: number = 30): Promise<AlertTrendData[]> => {
    try {
      const response = await api.get('/alerts', {
        params: { limit: 1000 }
      });
      const alerts = response.data;
      
      // Group alerts by date and type
      const dateMap = new Map<string, { low_stock: number; predicted_depletion: number }>();
      
      alerts.forEach((alert: any) => {
        const date = new Date(alert.created_at).toISOString().split('T')[0];
        const existing = dateMap.get(date) || { low_stock: 0, predicted_depletion: 0 };
        
        if (alert.alert_type === 'low_stock') {
          existing.low_stock += 1;
        } else if (alert.alert_type === 'predicted_depletion') {
          existing.predicted_depletion += 1;
        }
        
        dateMap.set(date, existing);
      });
      
      // Convert to array and sort by date
      const trendData = Array.from(dateMap.entries())
        .map(([date, data]) => ({
          date,
          low_stock: data.low_stock,
          predicted_depletion: data.predicted_depletion,
          total: data.low_stock + data.predicted_depletion,
        }))
        .sort((a, b) => a.date.localeCompare(b.date))
        .slice(-days); // Get last N days
      
      return trendData;
    } catch (error) {
      console.error('Error fetching alert trend:', error);
      return [];
    }
  },
};
