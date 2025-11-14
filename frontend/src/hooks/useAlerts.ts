import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { alertService } from '../services/alertService';
import type { AlertSettings } from '../types';
import toast from 'react-hot-toast';

// Query keys
export const alertKeys = {
  all: ['alerts'] as const,
  lists: () => [...alertKeys.all, 'list'] as const,
  settings: () => [...alertKeys.all, 'settings'] as const,
};

/**
 * Hook to fetch all alerts
 */
export function useAlerts() {
  return useQuery({
    queryKey: alertKeys.lists(),
    queryFn: () => alertService.getAlerts(),
    staleTime: 30000, // 30 seconds - alerts should be relatively fresh
    retry: 2,
    refetchInterval: 60000, // Refetch every minute to keep alerts up to date
  });
}

/**
 * Hook to fetch alert settings
 */
export function useAlertSettings() {
  return useQuery({
    queryKey: alertKeys.settings(),
    queryFn: () => alertService.getAlertSettings(),
    staleTime: 300000, // 5 minutes
    retry: 2,
  });
}

/**
 * Hook to acknowledge an alert
 */
export function useAcknowledgeAlert() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (alertId: string) => alertService.acknowledgeAlert(alertId),
    onSuccess: () => {
      // Invalidate alerts list to reflect the change
      queryClient.invalidateQueries({ queryKey: alertKeys.lists() });
      toast.success('Alert acknowledged');
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to acknowledge alert');
    },
    retry: 1,
  });
}

/**
 * Hook to resolve an alert
 */
export function useResolveAlert() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (alertId: string) => alertService.resolveAlert(alertId),
    onSuccess: () => {
      // Invalidate alerts list to reflect the change
      queryClient.invalidateQueries({ queryKey: alertKeys.lists() });
      toast.success('Alert resolved');
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to resolve alert');
    },
    retry: 1,
  });
}

/**
 * Hook to update alert settings
 */
export function useUpdateAlertSettings() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (settings: Partial<AlertSettings>) => 
      alertService.updateAlertSettings(settings),
    onSuccess: () => {
      // Invalidate settings to reflect the change
      queryClient.invalidateQueries({ queryKey: alertKeys.settings() });
      toast.success('Alert settings updated successfully');
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to update alert settings');
    },
    retry: 1,
  });
}
