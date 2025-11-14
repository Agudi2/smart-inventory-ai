import api from './api';

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

export const alertService = {
  // Get all alerts
  async getAlerts(): Promise<Alert[]> {
    const response = await api.get('/alerts');
    return response.data;
  },

  // Acknowledge an alert
  async acknowledgeAlert(alertId: string): Promise<Alert> {
    const response = await api.post(`/alerts/${alertId}/acknowledge`);
    return response.data;
  },

  // Resolve an alert
  async resolveAlert(alertId: string): Promise<Alert> {
    const response = await api.post(`/alerts/${alertId}/resolve`);
    return response.data;
  },

  // Get alert settings
  async getAlertSettings(): Promise<AlertSettings> {
    const response = await api.get('/alerts/settings');
    return response.data;
  },

  // Update alert settings
  async updateAlertSettings(settings: Partial<AlertSettings>): Promise<AlertSettings> {
    const response = await api.put('/alerts/settings', settings);
    return response.data;
  },
};
