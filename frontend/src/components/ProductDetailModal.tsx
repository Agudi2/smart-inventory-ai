import { useState } from 'react';
import { XMarkIcon, ChartBarIcon, ClockIcon, CurrencyDollarIcon } from '@heroicons/react/24/outline';
import { useQuery } from '@tanstack/react-query';
import { type Product } from '../services/productService';
import { predictionService } from '../services/predictionService';
import { vendorService } from '../services/vendorService';
import { inventoryService } from '../services/inventoryService';
import RestockPredictionChart from './RestockPredictionChart';

interface ProductDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  product: Product;
}

export default function ProductDetailModal({ isOpen, onClose, product }: ProductDetailModalProps) {
  const [activeTab, setActiveTab] = useState<'overview' | 'prediction' | 'history' | 'vendors'>('overview');

  // Fetch prediction data
  const { data: prediction, isLoading: predictionLoading, error: predictionError } = useQuery({
    queryKey: ['prediction', product.id],
    queryFn: () => predictionService.getPrediction(product.id),
    enabled: isOpen && activeTab === 'prediction',
    retry: false,
  });

  // Fetch vendor data
  const { data: vendors, isLoading: vendorsLoading } = useQuery({
    queryKey: ['vendors', product.id],
    queryFn: () => vendorService.getProductVendors(product.id),
    enabled: isOpen && activeTab === 'vendors',
  });

  // Fetch stock history
  const { data: history, isLoading: historyLoading } = useQuery({
    queryKey: ['history', product.id],
    queryFn: () => inventoryService.getProductHistory(product.id),
    enabled: isOpen && activeTab === 'history',
  });

  if (!isOpen) return null;

  // Get stock status color
  const getStockStatusColor = (status: string) => {
    switch (status) {
      case 'sufficient':
        return 'bg-green-100 text-green-800';
      case 'low':
        return 'bg-yellow-100 text-yellow-800';
      case 'critical':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  // Get confidence badge color
  const getConfidenceBadgeColor = (score?: number) => {
    if (!score) return 'bg-gray-100 text-gray-800';
    if (score >= 0.8) return 'bg-green-100 text-green-800';
    if (score >= 0.6) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
  };

  // Format date
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  // Format currency
  const formatCurrency = (amount?: number) => {
    if (amount === undefined || amount === null) return 'N/A';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative bg-white rounded-lg shadow-xl max-w-5xl w-full max-h-[90vh] overflow-hidden flex flex-col">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200">
            <div>
              <h2 className="text-2xl font-semibold text-gray-900">{product.name}</h2>
              <p className="text-sm text-gray-500 mt-1">SKU: {product.sku}</p>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <XMarkIcon className="w-6 h-6" />
            </button>
          </div>

          {/* Tabs */}
          <div className="border-b border-gray-200">
            <nav className="flex -mb-px px-6">
              <button
                onClick={() => setActiveTab('overview')}
                className={`py-4 px-4 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'overview'
                    ? 'border-primary-600 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Overview
              </button>
              <button
                onClick={() => setActiveTab('prediction')}
                className={`py-4 px-4 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'prediction'
                    ? 'border-primary-600 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <ChartBarIcon className="w-4 h-4 inline mr-1" />
                Prediction
              </button>
              <button
                onClick={() => setActiveTab('history')}
                className={`py-4 px-4 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'history'
                    ? 'border-primary-600 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <ClockIcon className="w-4 h-4 inline mr-1" />
                History
              </button>
              <button
                onClick={() => setActiveTab('vendors')}
                className={`py-4 px-4 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'vendors'
                    ? 'border-primary-600 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <CurrencyDollarIcon className="w-4 h-4 inline mr-1" />
                Vendors
              </button>
            </nav>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-6">
            {/* Overview Tab */}
            {activeTab === 'overview' && (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Product Information */}
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="text-lg font-medium text-gray-900 mb-4">Product Information</h3>
                    <dl className="space-y-3">
                      <div>
                        <dt className="text-sm font-medium text-gray-500">Category</dt>
                        <dd className="mt-1 text-sm text-gray-900">{product.category}</dd>
                      </div>
                      <div>
                        <dt className="text-sm font-medium text-gray-500">Barcode</dt>
                        <dd className="mt-1 text-sm text-gray-900">{product.barcode || 'N/A'}</dd>
                      </div>
                      <div>
                        <dt className="text-sm font-medium text-gray-500">Unit Cost</dt>
                        <dd className="mt-1 text-sm text-gray-900">{formatCurrency(product.unit_cost)}</dd>
                      </div>
                      <div>
                        <dt className="text-sm font-medium text-gray-500">Created</dt>
                        <dd className="mt-1 text-sm text-gray-900">{formatDate(product.created_at)}</dd>
                      </div>
                      <div>
                        <dt className="text-sm font-medium text-gray-500">Last Updated</dt>
                        <dd className="mt-1 text-sm text-gray-900">{formatDate(product.updated_at)}</dd>
                      </div>
                    </dl>
                  </div>

                  {/* Stock Information */}
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="text-lg font-medium text-gray-900 mb-4">Stock Information</h3>
                    <dl className="space-y-3">
                      <div>
                        <dt className="text-sm font-medium text-gray-500">Current Stock</dt>
                        <dd className="mt-1 text-2xl font-bold text-gray-900">{product.current_stock}</dd>
                      </div>
                      <div>
                        <dt className="text-sm font-medium text-gray-500">Reorder Threshold</dt>
                        <dd className="mt-1 text-sm text-gray-900">{product.reorder_threshold}</dd>
                      </div>
                      <div>
                        <dt className="text-sm font-medium text-gray-500">Stock Status</dt>
                        <dd className="mt-1">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStockStatusColor(product.stock_status)}`}>
                            {product.stock_status.charAt(0).toUpperCase() + product.stock_status.slice(1)}
                          </span>
                        </dd>
                      </div>
                      {product.predicted_depletion_date && (
                        <div>
                          <dt className="text-sm font-medium text-gray-500">Predicted Depletion</dt>
                          <dd className="mt-1 text-sm text-gray-900">
                            {new Date(product.predicted_depletion_date).toLocaleDateString('en-US', {
                              year: 'numeric',
                              month: 'long',
                              day: 'numeric',
                            })}
                          </dd>
                        </div>
                      )}
                    </dl>
                  </div>
                </div>
              </div>
            )}

            {/* Prediction Tab */}
            {activeTab === 'prediction' && (
              <div className="space-y-6">
                {predictionLoading && (
                  <div className="flex items-center justify-center h-64">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
                  </div>
                )}

                {predictionError && (
                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                    <p className="text-sm text-yellow-800">
                      Unable to load prediction data. This product may not have sufficient historical data for forecasting.
                    </p>
                  </div>
                )}

                {prediction && !predictionLoading && (
                  <>
                    {/* Prediction Summary */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="bg-blue-50 rounded-lg p-4">
                        <h4 className="text-sm font-medium text-blue-900 mb-1">Predicted Depletion</h4>
                        <p className="text-2xl font-bold text-blue-900">
                          {prediction.predicted_depletion_date
                            ? new Date(prediction.predicted_depletion_date).toLocaleDateString('en-US', {
                                month: 'short',
                                day: 'numeric',
                                year: 'numeric',
                              })
                            : 'N/A'}
                        </p>
                      </div>

                      <div className="bg-purple-50 rounded-lg p-4">
                        <h4 className="text-sm font-medium text-purple-900 mb-1">Daily Consumption</h4>
                        <p className="text-2xl font-bold text-purple-900">
                          {prediction.daily_consumption_rate
                            ? `${prediction.daily_consumption_rate.toFixed(2)} units/day`
                            : 'N/A'}
                        </p>
                      </div>

                      <div className="bg-green-50 rounded-lg p-4">
                        <h4 className="text-sm font-medium text-green-900 mb-1">Confidence Score</h4>
                        <div className="flex items-center gap-2">
                          <p className="text-2xl font-bold text-green-900">
                            {prediction.confidence_score
                              ? `${(prediction.confidence_score * 100).toFixed(0)}%`
                              : 'N/A'}
                          </p>
                          {prediction.confidence_score && (
                            <span className={`text-xs px-2 py-1 rounded-full ${getConfidenceBadgeColor(prediction.confidence_score)}`}>
                              {prediction.confidence_score >= 0.8 ? 'High' : prediction.confidence_score >= 0.6 ? 'Medium' : 'Low'}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Forecast Chart */}
                    <div className="bg-white border border-gray-200 rounded-lg p-4">
                      <h3 className="text-lg font-medium text-gray-900 mb-4">Stock Forecast</h3>
                      <RestockPredictionChart 
                        prediction={prediction} 
                        reorderThreshold={product.reorder_threshold}
                      />
                      <div className="mt-4 text-xs text-gray-500">
                        <p>Model: {prediction.model_type || 'Unknown'} | Version: {prediction.model_version || 'N/A'}</p>
                      </div>
                    </div>
                  </>
                )}
              </div>
            )}

            {/* History Tab */}
            {activeTab === 'history' && (
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Stock Movement History</h3>
                
                {historyLoading && (
                  <div className="flex items-center justify-center h-32">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
                  </div>
                )}

                {history && history.length === 0 && (
                  <div className="text-center py-8 text-gray-500">
                    No stock movements recorded yet.
                  </div>
                )}

                {history && history.length > 0 && (
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Date
                          </th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Type
                          </th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Quantity
                          </th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Previous
                          </th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            New Stock
                          </th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Reason
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {history.map((transaction) => (
                          <tr key={transaction.id} className="hover:bg-gray-50">
                            <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                              {formatDate(transaction.created_at)}
                            </td>
                            <td className="px-4 py-3 whitespace-nowrap text-sm">
                              <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                                transaction.transaction_type === 'addition' 
                                  ? 'bg-green-100 text-green-800'
                                  : transaction.transaction_type === 'removal'
                                  ? 'bg-red-100 text-red-800'
                                  : 'bg-blue-100 text-blue-800'
                              }`}>
                                {transaction.transaction_type}
                              </span>
                            </td>
                            <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                              {transaction.quantity > 0 ? '+' : ''}{transaction.quantity}
                            </td>
                            <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                              {transaction.previous_stock}
                            </td>
                            <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">
                              {transaction.new_stock}
                            </td>
                            <td className="px-4 py-3 text-sm text-gray-500">
                              {transaction.reason || '-'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}

            {/* Vendors Tab */}
            {activeTab === 'vendors' && (
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">Vendor Price Comparison</h3>
                
                {vendorsLoading && (
                  <div className="flex items-center justify-center h-32">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
                  </div>
                )}

                {vendors && vendors.length === 0 && (
                  <div className="text-center py-8 text-gray-500">
                    No vendors configured for this product yet.
                  </div>
                )}

                {vendors && vendors.length > 0 && (
                  <div className="overflow-x-auto">
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
                            Min Order
                          </th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Contact
                          </th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Status
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {vendors.map((vendor) => (
                          <tr 
                            key={vendor.id} 
                            className={`hover:bg-gray-50 ${vendor.is_recommended ? 'bg-green-50' : ''}`}
                          >
                            <td className="px-4 py-3 whitespace-nowrap">
                              <div className="text-sm font-medium text-gray-900">{vendor.vendor_name}</div>
                              {vendor.vendor_email && (
                                <div className="text-xs text-gray-500">{vendor.vendor_email}</div>
                              )}
                            </td>
                            <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">
                              {formatCurrency(vendor.unit_price)}
                            </td>
                            <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                              {vendor.lead_time_days} days
                            </td>
                            <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                              {vendor.minimum_order_quantity} units
                            </td>
                            <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                              {vendor.vendor_phone || '-'}
                            </td>
                            <td className="px-4 py-3 whitespace-nowrap">
                              {vendor.is_recommended && (
                                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                  Recommended
                                </span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="border-t border-gray-200 px-6 py-4 bg-gray-50">
            <button
              onClick={onClose}
              className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
