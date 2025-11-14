import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { barcodeService } from '../services/barcodeService';
import type { BarcodeLinkRequest } from '../types';
import toast from 'react-hot-toast';
import { productKeys } from './useProducts';

// Query keys
export const barcodeKeys = {
  all: ['barcode'] as const,
  lookup: (code: string) => [...barcodeKeys.all, 'lookup', code] as const,
};

/**
 * Hook to lookup a product by barcode
 */
export function useBarcodeLookup(code: string, enabled = false) {
  return useQuery({
    queryKey: barcodeKeys.lookup(code),
    queryFn: () => barcodeService.lookupBarcode(code),
    enabled: enabled && !!code,
    staleTime: 300000, // 5 minutes - barcodes don't change often
    retry: 1,
  });
}

/**
 * Hook to scan a barcode
 */
export function useScanBarcode() {
  return useMutation({
    mutationFn: (barcode: string) => barcodeService.scanBarcode(barcode),
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to scan barcode');
    },
    retry: 1,
  });
}

/**
 * Hook to link a barcode to a product
 */
export function useLinkBarcode() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: BarcodeLinkRequest) => barcodeService.linkBarcode(data),
    onSuccess: (response) => {
      // Invalidate product queries to reflect the new barcode
      queryClient.invalidateQueries({ queryKey: productKeys.detail(response.product_id) });
      queryClient.invalidateQueries({ queryKey: productKeys.lists() });
      // Invalidate barcode lookup for this code
      queryClient.invalidateQueries({ queryKey: barcodeKeys.all });
      toast.success(response.message || 'Barcode linked successfully');
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to link barcode');
    },
    retry: 1,
  });
}
