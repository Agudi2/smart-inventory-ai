import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { inventoryService } from '../services/inventoryService';
import type { StockAdjustment } from '../types';
import toast from 'react-hot-toast';
import { productKeys } from './useProducts';

// Query keys
export const inventoryKeys = {
  all: ['inventory'] as const,
  movements: () => [...inventoryKeys.all, 'movements'] as const,
  movementsList: (productId?: string) => [...inventoryKeys.movements(), productId] as const,
  history: (productId: string) => [...inventoryKeys.all, 'history', productId] as const,
};

/**
 * Hook to fetch stock movements with optional product filter
 */
export function useInventoryMovements(productId?: string) {
  return useQuery({
    queryKey: inventoryKeys.movementsList(productId),
    queryFn: () => inventoryService.getMovements(productId),
    staleTime: 30000, // 30 seconds
    retry: 2,
  });
}

/**
 * Hook to fetch stock movement history for a specific product
 */
export function useProductHistory(productId: string, enabled = true) {
  return useQuery({
    queryKey: inventoryKeys.history(productId),
    queryFn: () => inventoryService.getProductHistory(productId),
    enabled: enabled && !!productId,
    staleTime: 30000, // 30 seconds
    retry: 2,
  });
}

/**
 * Hook to adjust stock level
 */
export function useAdjustStock() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: StockAdjustment) => inventoryService.adjustStock(data),
    onSuccess: (transaction) => {
      // Invalidate inventory movements
      queryClient.invalidateQueries({ queryKey: inventoryKeys.movements() });
      // Invalidate product history for this specific product
      queryClient.invalidateQueries({ queryKey: inventoryKeys.history(transaction.product_id) });
      // Invalidate products list to update stock levels
      queryClient.invalidateQueries({ queryKey: productKeys.lists() });
      // Invalidate specific product detail
      queryClient.invalidateQueries({ queryKey: productKeys.detail(transaction.product_id) });
      
      const action = transaction.quantity > 0 ? 'added to' : 'removed from';
      toast.success(`Stock ${action} successfully`);
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to adjust stock');
    },
    retry: 1,
  });
}
