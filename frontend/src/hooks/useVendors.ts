import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { vendorService } from '../services/vendorService';
import type { 
  VendorCreate, 
  VendorUpdate, 
  VendorPriceCreate,
  VendorPriceUpdate 
} from '../types';
import toast from 'react-hot-toast';

// Query keys
export const vendorKeys = {
  all: ['vendors'] as const,
  lists: () => [...vendorKeys.all, 'list'] as const,
  list: (skip?: number, limit?: number) => [...vendorKeys.lists(), skip, limit] as const,
  details: () => [...vendorKeys.all, 'detail'] as const,
  detail: (id: string) => [...vendorKeys.details(), id] as const,
  productVendors: (productId: string) => [...vendorKeys.all, 'product', productId] as const,
};

/**
 * Hook to fetch all vendors
 */
export function useVendors(skip = 0, limit = 100) {
  return useQuery({
    queryKey: vendorKeys.list(skip, limit),
    queryFn: () => vendorService.getAllVendors(skip, limit),
    staleTime: 60000, // 1 minute
    retry: 2,
  });
}

/**
 * Hook to fetch a single vendor by ID
 */
export function useVendor(vendorId: string, enabled = true) {
  return useQuery({
    queryKey: vendorKeys.detail(vendorId),
    queryFn: () => vendorService.getVendor(vendorId),
    enabled: enabled && !!vendorId,
    staleTime: 60000, // 1 minute
    retry: 2,
  });
}

/**
 * Hook to fetch vendors for a specific product
 */
export function useProductVendors(productId: string, enabled = true) {
  return useQuery({
    queryKey: vendorKeys.productVendors(productId),
    queryFn: () => vendorService.getProductVendors(productId),
    enabled: enabled && !!productId,
    staleTime: 60000, // 1 minute
    retry: 2,
  });
}

/**
 * Hook to create a new vendor
 */
export function useCreateVendor() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: VendorCreate) => vendorService.createVendor(data),
    onSuccess: (newVendor) => {
      queryClient.invalidateQueries({ queryKey: vendorKeys.lists() });
      toast.success(`Vendor "${newVendor.name}" created successfully`);
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to create vendor');
    },
    retry: 1,
  });
}

/**
 * Hook to update a vendor
 */
export function useUpdateVendor() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ vendorId, data }: { vendorId: string; data: VendorUpdate }) =>
      vendorService.updateVendor(vendorId, data),
    onSuccess: (updatedVendor) => {
      queryClient.invalidateQueries({ queryKey: vendorKeys.lists() });
      queryClient.invalidateQueries({ queryKey: vendorKeys.detail(updatedVendor.id) });
      toast.success(`Vendor "${updatedVendor.name}" updated successfully`);
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to update vendor');
    },
    retry: 1,
  });
}

/**
 * Hook to delete a vendor
 */
export function useDeleteVendor() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (vendorId: string) => vendorService.deleteVendor(vendorId),
    onSuccess: (_, deletedId) => {
      queryClient.invalidateQueries({ queryKey: vendorKeys.lists() });
      queryClient.removeQueries({ queryKey: vendorKeys.detail(deletedId) });
      toast.success('Vendor deleted successfully');
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to delete vendor');
    },
    retry: 1,
  });
}

/**
 * Hook to add or update vendor price for a product
 */
export function useAddVendorPrice() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ vendorId, data }: { vendorId: string; data: VendorPriceCreate }) =>
      vendorService.addVendorPrice(vendorId, data),
    onSuccess: (vendorPrice) => {
      // Invalidate product vendors list
      queryClient.invalidateQueries({ 
        queryKey: vendorKeys.productVendors(vendorPrice.product_id) 
      });
      toast.success('Vendor price added successfully');
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to add vendor price');
    },
    retry: 1,
  });
}

/**
 * Hook to update vendor price
 */
export function useUpdateVendorPrice() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ 
      vendorId, 
      productId, 
      data 
    }: { 
      vendorId: string; 
      productId: string; 
      data: VendorPriceUpdate 
    }) => vendorService.updateVendorPrice(vendorId, productId, data),
    onSuccess: (vendorPrice) => {
      queryClient.invalidateQueries({ 
        queryKey: vendorKeys.productVendors(vendorPrice.product_id) 
      });
      toast.success('Vendor price updated successfully');
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to update vendor price');
    },
    retry: 1,
  });
}
