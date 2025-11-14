import { type ReactNode } from 'react';
import {
  CubeIcon,
  BellAlertIcon,
  BuildingStorefrontIcon,
  MagnifyingGlassIcon,
} from '@heroicons/react/24/outline';

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description: string;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export default function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="bg-white rounded-lg shadow p-12">
      <div className="text-center">
        <div className="flex items-center justify-center w-12 h-12 mx-auto bg-gray-100 rounded-full">
          {icon || <CubeIcon className="w-6 h-6 text-gray-400" />}
        </div>
        
        <h3 className="mt-4 text-lg font-medium text-gray-900">{title}</h3>
        
        <p className="mt-2 text-sm text-gray-600 max-w-md mx-auto">{description}</p>

        {action && (
          <button
            onClick={action.onClick}
            className="mt-6 inline-flex items-center px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 transition-colors"
          >
            {action.label}
          </button>
        )}
      </div>
    </div>
  );
}

// Preset empty states for common scenarios
export function EmptyProductsState({ onAddProduct }: { onAddProduct?: () => void }) {
  return (
    <EmptyState
      icon={<CubeIcon className="w-6 h-6 text-gray-400" />}
      title="No products yet"
      description="Get started by adding your first product to the inventory."
      action={
        onAddProduct
          ? {
              label: 'Add Product',
              onClick: onAddProduct,
            }
          : undefined
      }
    />
  );
}

export function EmptyAlertsState() {
  return (
    <EmptyState
      icon={<BellAlertIcon className="w-6 h-6 text-gray-400" />}
      title="No alerts"
      description="All clear! No active alerts at the moment."
    />
  );
}

export function EmptyVendorsState({ onAddVendor }: { onAddVendor?: () => void }) {
  return (
    <EmptyState
      icon={<BuildingStorefrontIcon className="w-6 h-6 text-gray-400" />}
      title="No vendors yet"
      description="Add vendors to track pricing and manage your suppliers."
      action={
        onAddVendor
          ? {
              label: 'Add Vendor',
              onClick: onAddVendor,
            }
          : undefined
      }
    />
  );
}

export function EmptySearchState({ searchTerm }: { searchTerm: string }) {
  return (
    <EmptyState
      icon={<MagnifyingGlassIcon className="w-6 h-6 text-gray-400" />}
      title="No results found"
      description={`No items match your search for "${searchTerm}". Try adjusting your filters.`}
    />
  );
}
