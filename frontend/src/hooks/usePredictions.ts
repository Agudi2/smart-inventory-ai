import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { predictionService } from '../services/predictionService';
import toast from 'react-hot-toast';

// Query keys
export const predictionKeys = {
  all: ['predictions'] as const,
  detail: (productId: string, forecastDays?: number) => 
    [...predictionKeys.all, productId, forecastDays] as const,
};

/**
 * Hook to fetch stock depletion prediction for a product
 */
export function usePrediction(productId: string, forecastDays = 90, enabled = true) {
  return useQuery({
    queryKey: predictionKeys.detail(productId, forecastDays),
    queryFn: () => predictionService.getPrediction(productId, forecastDays),
    enabled: enabled && !!productId,
    staleTime: 3600000, // 1 hour - predictions are cached on backend
    retry: 2,
    // Don't show error toast for predictions - they might not exist for all products
    meta: {
      suppressErrorToast: true,
    },
  });
}

/**
 * Hook to manually trigger prediction refresh
 */
export function useRefreshPrediction() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (productId: string) => {
      // This would call a train endpoint if available
      // For now, we'll just invalidate the cache to force a refetch
      return { productId };
    },
    onSuccess: (data) => {
      // Invalidate prediction cache for this product
      queryClient.invalidateQueries({ 
        queryKey: predictionKeys.all,
        predicate: (query) => {
          const [, id] = query.queryKey;
          return id === data.productId;
        }
      });
      toast.success('Prediction refreshed');
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to refresh prediction');
    },
  });
}
