import { useState, useEffect } from 'react';
import { useZxing } from 'react-zxing';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { XMarkIcon, CheckCircleIcon } from '@heroicons/react/24/outline';
import { barcodeService, type BarcodeScanResponse } from '../services/barcodeService';
import { inventoryService } from '../services/inventoryService';
import { productService, type ProductCreate } from '../services/productService';

interface BarcodeScannerModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function BarcodeScannerModal({ isOpen, onClose }: BarcodeScannerModalProps) {
  const queryClient = useQueryClient();
  const [scannedData, setScannedData] = useState<BarcodeScanResponse | null>(null);
  const [isScanning, setIsScanning] = useState(true);
  const [stockQuantity, setStockQuantity] = useState<number>(1);
  const [adjustmentReason, setAdjustmentReason] = useState<string>('Barcode scan');
  const [isProcessing, setIsProcessing] = useState(false);

  // Barcode scanning hook
  const { ref } = useZxing({
    onDecodeResult(result) {
      if (isScanning && !scannedData) {
        const barcodeValue = result.getText();
        handleBarcodeScan(barcodeValue);
      }
    },
    onError(error) {
      console.error('Barcode scanning error:', error);
    },
  });

  // Reset state when modal opens/closes
  useEffect(() => {
    if (isOpen) {
      setScannedData(null);
      setIsScanning(true);
      setStockQuantity(1);
      setAdjustmentReason('Barcode scan');
      setIsProcessing(false);
    }
  }, [isOpen]);

  // Scan barcode mutation
  const scanMutation = useMutation({
    mutationFn: (barcode: string) => barcodeService.scanBarcode(barcode),
    onSuccess: (data) => {
      setScannedData(data);
      setIsScanning(false);
      
      if (data.found) {
        toast.success(`Product found: ${data.product_name}`);
      } else if (data.external_info) {
        toast.success('Product info retrieved from external database');
      } else {
        toast.error('Product not found');
      }
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to scan barcode');
      setIsScanning(true);
    },
  });

  // Stock adjustment mutation
  const adjustStockMutation = useMutation({
    mutationFn: (data: { product_id: string; quantity: number; reason?: string }) =>
      inventoryService.adjustStock(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] });
      toast.success('Stock updated successfully');
      onClose();
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update stock');
    },
  });

  // Create product mutation
  const createProductMutation = useMutation({
    mutationFn: (data: ProductCreate) => productService.createProduct(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] });
      toast.success('Product created successfully');
      onClose();
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to create product');
    },
  });

  const handleBarcodeScan = async (barcode: string) => {
    setIsProcessing(true);
    try {
      await scanMutation.mutateAsync(barcode);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleStockAdjustment = () => {
    if (!scannedData?.product_id) {
      toast.error('No product selected');
      return;
    }

    if (stockQuantity === 0) {
      toast.error('Quantity cannot be zero');
      return;
    }

    adjustStockMutation.mutate({
      product_id: scannedData.product_id,
      quantity: stockQuantity,
      reason: adjustmentReason || undefined,
    });
  };

  const handleCreateProduct = () => {
    if (!scannedData?.external_info) {
      toast.error('No product information available');
      return;
    }

    const externalInfo = scannedData.external_info;
    
    // Generate SKU from barcode
    const sku = `SKU-${externalInfo.barcode}`;
    
    createProductMutation.mutate({
      sku,
      name: externalInfo.title || 'Unknown Product',
      category: externalInfo.category || 'Uncategorized',
      current_stock: stockQuantity > 0 ? stockQuantity : 0,
      reorder_threshold: 10,
      barcode: externalInfo.barcode,
    });
  };

  const handleRescan = () => {
    setScannedData(null);
    setIsScanning(true);
    setStockQuantity(1);
    setAdjustmentReason('Barcode scan');
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-screen items-center justify-center p-4">
        {/* Backdrop */}
        <div
          className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
          onClick={onClose}
        />

        {/* Modal */}
        <div className="relative bg-white rounded-lg shadow-xl max-w-2xl w-full">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b">
            <h2 className="text-xl font-semibold text-gray-900">
              Barcode Scanner
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>

          {/* Content */}
          <div className="p-6">
            {isScanning && !scannedData && (
              <div className="space-y-4">
                <div className="relative bg-black rounded-lg overflow-hidden aspect-video">
                  <video ref={ref} className="w-full h-full object-cover" />
                  
                  {/* Scanning overlay */}
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="border-4 border-primary-500 rounded-lg w-64 h-48 relative">
                      <div className="absolute top-0 left-0 w-8 h-8 border-t-4 border-l-4 border-white"></div>
                      <div className="absolute top-0 right-0 w-8 h-8 border-t-4 border-r-4 border-white"></div>
                      <div className="absolute bottom-0 left-0 w-8 h-8 border-b-4 border-l-4 border-white"></div>
                      <div className="absolute bottom-0 right-0 w-8 h-8 border-b-4 border-r-4 border-white"></div>
                    </div>
                  </div>
                </div>
                
                <p className="text-center text-gray-600">
                  {isProcessing ? 'Processing barcode...' : 'Position barcode within the frame'}
                </p>
              </div>
            )}

            {scannedData && (
              <div className="space-y-6">
                {/* Scan Success Indicator */}
                <div className="flex items-center justify-center space-x-2 text-green-600">
                  <CheckCircleIcon className="h-8 w-8" />
                  <span className="text-lg font-medium">Barcode Scanned Successfully</span>
                </div>

                {/* Product Information */}
                {scannedData.found ? (
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                    <h3 className="font-semibold text-green-900 mb-2">Product Found</h3>
                    <div className="space-y-1 text-sm text-green-800">
                      <p><span className="font-medium">Name:</span> {scannedData.product_name}</p>
                      <p><span className="font-medium">Current Stock:</span> {scannedData.current_stock}</p>
                    </div>
                  </div>
                ) : scannedData.external_info ? (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <h3 className="font-semibold text-blue-900 mb-2">Product Not in Database</h3>
                    <p className="text-sm text-blue-800 mb-3">
                      Product information retrieved from external database. You can create a new product.
                    </p>
                    <div className="space-y-1 text-sm text-blue-800">
                      {scannedData.external_info.title && (
                        <p><span className="font-medium">Title:</span> {scannedData.external_info.title}</p>
                      )}
                      {scannedData.external_info.brand && (
                        <p><span className="font-medium">Brand:</span> {scannedData.external_info.brand}</p>
                      )}
                      {scannedData.external_info.category && (
                        <p><span className="font-medium">Category:</span> {scannedData.external_info.category}</p>
                      )}
                      <p><span className="font-medium">Barcode:</span> {scannedData.external_info.barcode}</p>
                    </div>
                  </div>
                ) : (
                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                    <h3 className="font-semibold text-yellow-900 mb-2">Product Not Found</h3>
                    <p className="text-sm text-yellow-800">
                      This product is not in your database and no external information is available.
                    </p>
                  </div>
                )}

                {/* Stock Adjustment Form */}
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Quantity
                    </label>
                    <input
                      type="number"
                      value={stockQuantity}
                      onChange={(e) => setStockQuantity(parseInt(e.target.value) || 0)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                      placeholder="Enter quantity"
                    />
                    <p className="mt-1 text-xs text-gray-500">
                      Use positive numbers to add stock, negative to remove
                    </p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Reason (Optional)
                    </label>
                    <input
                      type="text"
                      value={adjustmentReason}
                      onChange={(e) => setAdjustmentReason(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                      placeholder="e.g., Barcode scan, Restock, etc."
                    />
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex space-x-3">
                  {scannedData.found ? (
                    <button
                      onClick={handleStockAdjustment}
                      disabled={adjustStockMutation.isPending}
                      className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                    >
                      {adjustStockMutation.isPending ? 'Updating...' : 'Update Stock'}
                    </button>
                  ) : scannedData.external_info ? (
                    <button
                      onClick={handleCreateProduct}
                      disabled={createProductMutation.isPending}
                      className="flex-1 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                    >
                      {createProductMutation.isPending ? 'Creating...' : 'Create Product'}
                    </button>
                  ) : null}
                  
                  <button
                    onClick={handleRescan}
                    className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors"
                  >
                    Scan Again
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
