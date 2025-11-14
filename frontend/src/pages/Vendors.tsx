import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import DashboardLayout from '../components/DashboardLayout';
import VendorFormModal from '../components/VendorFormModal';
import { vendorService, type Vendor } from '../services/vendorService';
import {
  BuildingStorefrontIcon,
  PencilIcon,
  TrashIcon,
  PlusIcon,
  EnvelopeIcon,
  PhoneIcon,
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import { TableSkeleton } from '../components/LoadingSkeleton';
import ErrorState from '../components/ErrorState';
import { EmptyVendorsState } from '../components/EmptyState';

export default function Vendors() {
  const queryClient = useQueryClient();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedVendor, setSelectedVendor] = useState<Vendor | null>(null);
  const [modalMode, setModalMode] = useState<'create' | 'edit'>('create');
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);

  // Fetch vendors
  const { data: vendors, isLoading, error, refetch } = useQuery({
    queryKey: ['vendors'],
    queryFn: () => vendorService.getAllVendors(),
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (vendorId: string) => vendorService.deleteVendor(vendorId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vendors'] });
      toast.success('Vendor deleted successfully');
      setDeleteConfirm(null);
    },
    onError: (error: any) => {
      const errorMessage = error.response?.data?.detail || 'Failed to delete vendor';
      toast.error(errorMessage);
    },
  });

  // Handle add vendor
  const handleAddVendor = () => {
    setSelectedVendor(null);
    setModalMode('create');
    setIsModalOpen(true);
  };

  // Handle edit vendor
  const handleEditVendor = (vendor: Vendor) => {
    setSelectedVendor(vendor);
    setModalMode('edit');
    setIsModalOpen(true);
  };

  // Handle delete vendor
  const handleDeleteVendor = (vendorId: string) => {
    if (deleteConfirm === vendorId) {
      deleteMutation.mutate(vendorId);
    } else {
      setDeleteConfirm(vendorId);
      setTimeout(() => setDeleteConfirm(null), 3000);
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Vendors</h1>
            <p className="mt-1 text-sm text-gray-600">
              Manage your suppliers and vendor relationships
            </p>
          </div>
          <button
            onClick={handleAddVendor}
            className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 transition-colors flex items-center gap-2"
          >
            <PlusIcon className="h-5 w-5" />
            Add Vendor
          </button>
        </div>

        {/* Loading State */}
        {isLoading && <TableSkeleton rows={5} columns={5} />}

        {/* Error State */}
        {error && (
          <ErrorState
            title="Failed to Load Vendors"
            message="We couldn't load your vendors. Please check your connection and try again."
            onRetry={() => refetch()}
          />
        )}

        {/* Empty State */}
        {!isLoading && !error && (!vendors || vendors.length === 0) && (
          <EmptyVendorsState onAddVendor={handleAddVendor} />
        )}

        {/* Vendor List */}
        {!isLoading && !error && vendors && vendors.length > 0 && (
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Vendor Name
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Contact
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Products
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Added
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {vendors.map((vendor) => (
                    <tr key={vendor.id} className="hover:bg-gray-50 transition-colors">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="flex-shrink-0 h-10 w-10 bg-primary-100 rounded-full flex items-center justify-center">
                            <BuildingStorefrontIcon className="h-6 w-6 text-primary-600" />
                          </div>
                          <div className="ml-4">
                            <div className="text-sm font-medium text-gray-900">
                              {vendor.name}
                            </div>
                            {vendor.address && (
                              <div className="text-xs text-gray-500 truncate max-w-xs">
                                {vendor.address}
                              </div>
                            )}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="space-y-1">
                          {vendor.contact_email && (
                            <div className="flex items-center text-sm text-gray-600">
                              <EnvelopeIcon className="h-4 w-4 mr-2 text-gray-400" />
                              <a
                                href={`mailto:${vendor.contact_email}`}
                                className="hover:text-primary-600 transition-colors"
                              >
                                {vendor.contact_email}
                              </a>
                            </div>
                          )}
                          {vendor.contact_phone && (
                            <div className="flex items-center text-sm text-gray-600">
                              <PhoneIcon className="h-4 w-4 mr-2 text-gray-400" />
                              <a
                                href={`tel:${vendor.contact_phone}`}
                                className="hover:text-primary-600 transition-colors"
                              >
                                {vendor.contact_phone}
                              </a>
                            </div>
                          )}
                          {!vendor.contact_email && !vendor.contact_phone && (
                            <span className="text-sm text-gray-400">No contact info</span>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                          {vendor.product_count || 0} {vendor.product_count === 1 ? 'product' : 'products'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(vendor.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => handleEditVendor(vendor)}
                            className="text-primary-600 hover:text-primary-900 transition-colors p-1"
                            title="Edit vendor"
                          >
                            <PencilIcon className="h-5 w-5" />
                          </button>
                          <button
                            onClick={() => handleDeleteVendor(vendor.id)}
                            disabled={deleteMutation.isPending}
                            className={`p-1 transition-colors ${
                              deleteConfirm === vendor.id
                                ? 'text-red-600 hover:text-red-900'
                                : 'text-gray-400 hover:text-red-600'
                            } disabled:opacity-50`}
                            title={deleteConfirm === vendor.id ? 'Click again to confirm' : 'Delete vendor'}
                          >
                            <TrashIcon className="h-5 w-5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Vendor count */}
        {!isLoading && vendors && vendors.length > 0 && (
          <div className="text-sm text-gray-500">
            Showing {vendors.length} {vendors.length === 1 ? 'vendor' : 'vendors'}
          </div>
        )}
      </div>

      {/* Vendor Form Modal */}
      <VendorFormModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        vendor={selectedVendor}
        mode={modalMode}
      />
    </DashboardLayout>
  );
}
