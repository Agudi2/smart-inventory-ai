import api from './api';

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

export const barcodeService = {
  /**
   * Scan a barcode and get product information
   */
  async scanBarcode(barcode: string): Promise<BarcodeScanResponse> {
    const response = await api.post<BarcodeScanResponse>('/barcode/scan', {
      barcode,
    });
    return response.data;
  },

  /**
   * Lookup a product by barcode
   */
  async lookupBarcode(code: string): Promise<BarcodeScanResponse> {
    const response = await api.get<BarcodeScanResponse>(`/barcode/lookup/${code}`);
    return response.data;
  },

  /**
   * Link a barcode to an existing product
   */
  async linkBarcode(data: BarcodeLinkRequest): Promise<BarcodeLinkResponse> {
    const response = await api.post<BarcodeLinkResponse>('/barcode/link', data);
    return response.data;
  },
};
