import api from './api';

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

export const predictionService = {
  /**
   * Get stock depletion prediction for a specific product
   */
  async getPrediction(productId: string, forecastDays: number = 90): Promise<PredictionResult> {
    const response = await api.get<PredictionResult>(`/predictions/${productId}`, {
      params: { forecast_days: forecastDays, use_cache: true }
    });
    return response.data;
  },
};
