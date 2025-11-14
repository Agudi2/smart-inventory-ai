import { useQuery } from '@tanstack/react-query';
import { vendorService } from '../services/vendorService';
import { CheckBadgeIcon, ClockIcon, ShoppingCartIcon } from '@heroicons/react/24/outline';

interface VendorComparisonProps {
  productId: string;
}

export default function VendorComparison({ productId }: VendorComparisonProps) {
  const { data: vendors, isLoading, error } = useQuery({
    queryKey: ['product-vendors', productId],
    queryFn: () => vendorService.getProductVendors(productId),
  });

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-3">
        <div className="h-4 bg-gray-200 rounded w-1/4"></div>
        <div className="h-20 bg-gray-200 rounded"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-sm text-red-600">
        Failed to load vendor information
      </div>
    );
  }

  if (!vendors || vendors.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <ShoppingCartIcon className="mx-auto h-12 w-12 text-gray-400 mb-2" />
        <p className="text-sm">No vendors available for this product</p>
        <p className="text-xs text-gray-400 mt-1">Add vendor pricing to see comparisons</p>
      </div>
    );
  }

  // Sort vendors by price (lowest first)
  const sortedVendors = [...vendors].sort((a, b) => a.unit_price - b.unit_price);

  return (
    <div className="space-y-4">
      <h3 className="text-sm font-medium text-gray-900">Vendor Price Comparison</h3>
      
      <div className="overflow-hidden border border-gray-200 rounded-lg">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Vendor
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Unit Price
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Lead Time
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Min. Order
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {sortedVendors.map((vendor, index) => {
              const isRecommended = index === 0; // Lowest price is recommended
              
              return (
                <tr key={vendor.id} className={isRecommended ? 'bg-green-50' : ''}>
                  <td className="px-4 py-3 whitespace-nowrap">
                    <div className="flex flex-col">
                      <div className="text-sm font-medium text-gray-900">
                        {vendor.vendor_name || 'Unknown Vendor'}
                      </div>
                      {vendor.vendor_email && (
                        <div className="text-xs text-gray-500">{vendor.vendor_email}</div>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    <div className="text-sm font-semibold text-gray-900">
                      ${vendor.unit_price.toFixed(2)}
                    </div>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    <div className="flex items-center text-sm text-gray-600">
                      <ClockIcon className="h-4 w-4 mr-1 text-gray-400" />
                      {vendor.lead_time_days} {vendor.lead_time_days === 1 ? 'day' : 'days'}
                    </div>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    <div className="text-sm text-gray-600">
                      {vendor.minimum_order_quantity} {vendor.minimum_order_quantity === 1 ? 'unit' : 'units'}
                    </div>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    {isRecommended && (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        <CheckBadgeIcon className="h-4 w-4 mr-1" />
                        Recommended
                      </span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="text-xs text-gray-500 mt-2">
        <p>* Recommended vendor is based on the lowest unit price</p>
        <p className="mt-1">Last updated: {new Date(sortedVendors[0]?.last_updated).toLocaleDateString()}</p>
      </div>
    </div>
  );
}
