import { useState, useEffect } from 'react';
import { XMarkIcon, PlusIcon, TrashIcon } from '@heroicons/react/24/outline';
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query';
import { productService, type Product, type ProductCreate, type ProductUpdate } from '../services/productService';
import { vendorService } from '../services/vendorService';
import toast from 'react-hot-toast';

interface ProductFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  product?: Product | null;
  mode: 'create' | 'edit';
}

interface FormData {
  sku: string;
  name: string;
  category: string;
  current_stock: string;
  reorder_threshold: string;
  barcode: string;
  unit_cost: string;
}

interface FormErrors {
  sku?: string;
  name?: string;
  category?: string;
  current_stock?: string;
  reorder_threshold?: string;
  barcode?: string;
  unit_cost?: string;
}

interface VendorPriceEntry {
  vendor_id: string;
  unit_price: string;
  lead_time_days: string;
  minimum_order_quantity: string;
}

export default function ProductFormModal({ isOpen, onClose, product, mode }: ProductFormModalProps) {
  const queryClient = useQueryClient();

  const [formData, setFormData] = useState<FormData>({
    sku: '',
    name: '',
    category: '',
    current_stock: '0',
    reorder_threshold: '10',
    barcode: '',
    unit_cost: '',
  });

  const [errors, setErrors] = useState<FormErrors>({});
  const [touched, setTouched] = useState<Record<string, boolean>>({});
  const [vendorPrices, setVendorPrices] = useState<VendorPriceEntry[]>([]);
  const [showVendorSection, setShowVendorSection] = useState(false);

  // Fetch vendors
  const { data: vendors } = useQuery({
    queryKey: ['vendors'],
    queryFn: () => vendorService.getAllVendors(),
    enabled: isOpen,
  });

  // Initialize form data when product changes
  useEffect(() => {
    if (mode === 'edit' && product) {
      setFormData({
        sku: product.sku,
        name: product.name,
        category: product.category,
        current_stock: product.current_stock.toString(),
        reorder_threshold: product.reorder_threshold.toString(),
        barcode: product.barcode || '',
        unit_cost: product.unit_cost?.toString() || '',
      });
    } else if (mode === 'create') {
      setFormData({
        sku: '',
        name: '',
        category: '',
        current_stock: '0',
        reorder_threshold: '10',
        barcode: '',
        unit_cost: '',
      });
    }
    setErrors({});
    setTouched({});
    setVendorPrices([]);
    setShowVendorSection(false);
  }, [mode, product, isOpen]);

  // Add vendor price entry
  const addVendorPrice = () => {
    setVendorPrices([
      ...vendorPrices,
      {
        vendor_id: '',
        unit_price: '',
        lead_time_days: '7',
        minimum_order_quantity: '1',
      },
    ]);
  };

  // Remove vendor price entry
  const removeVendorPrice = (index: number) => {
    setVendorPrices(vendorPrices.filter((_, i) => i !== index));
  };

  // Update vendor price entry
  const updateVendorPrice = (index: number, field: keyof VendorPriceEntry, value: string) => {
    const updated = [...vendorPrices];
    updated[index] = { ...updated[index], [field]: value };
    setVendorPrices(updated);
  };

  // Create mutation
  const createMutation = useMutation({
    mutationFn: async (data: ProductCreate) => {
      const product = await productService.createProduct(data);
      
      // Add vendor prices if any
      if (vendorPrices.length > 0) {
        await Promise.all(
          vendorPrices.map((vp) =>
            vendorService.addVendorPrice(vp.vendor_id, {
              product_id: product.id,
              unit_price: parseFloat(vp.unit_price),
              lead_time_days: parseInt(vp.lead_time_days) || 7,
              minimum_order_quantity: parseInt(vp.minimum_order_quantity) || 1,
            })
          )
        );
      }
      
      return product;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] });
      queryClient.invalidateQueries({ queryKey: ['product-vendors'] });
      toast.success('Product created successfully');
      onClose();
    },
    onError: (error: any) => {
      const errorMessage = error.response?.data?.detail || 'Failed to create product';
      toast.error(errorMessage);
    },
  });

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: ProductUpdate }) =>
      productService.updateProduct(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] });
      toast.success('Product updated successfully');
      onClose();
    },
    onError: (error: any) => {
      const errorMessage = error.response?.data?.detail || 'Failed to update product';
      toast.error(errorMessage);
    },
  });

  // Validate form
  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    // SKU validation (required for create mode)
    if (mode === 'create' && !formData.sku.trim()) {
      newErrors.sku = 'SKU is required';
    }

    // Name validation (required)
    if (!formData.name.trim()) {
      newErrors.name = 'Product name is required';
    }

    // Category validation (required)
    if (!formData.category.trim()) {
      newErrors.category = 'Category is required';
    }

    // Current stock validation (required, must be non-negative integer)
    const currentStock = parseInt(formData.current_stock);
    if (formData.current_stock === '' || isNaN(currentStock)) {
      newErrors.current_stock = 'Current stock must be a number';
    } else if (currentStock < 0) {
      newErrors.current_stock = 'Current stock cannot be negative';
    }

    // Reorder threshold validation (required, must be non-negative integer)
    const reorderThreshold = parseInt(formData.reorder_threshold);
    if (formData.reorder_threshold === '' || isNaN(reorderThreshold)) {
      newErrors.reorder_threshold = 'Reorder threshold must be a number';
    } else if (reorderThreshold < 0) {
      newErrors.reorder_threshold = 'Reorder threshold cannot be negative';
    }

    // Unit cost validation (optional, must be positive if provided)
    if (formData.unit_cost) {
      const unitCost = parseFloat(formData.unit_cost);
      if (isNaN(unitCost)) {
        newErrors.unit_cost = 'Unit cost must be a valid number';
      } else if (unitCost < 0) {
        newErrors.unit_cost = 'Unit cost cannot be negative';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handle input change
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    
    // Clear error for this field when user starts typing
    if (errors[name as keyof FormErrors]) {
      setErrors((prev) => ({ ...prev, [name]: undefined }));
    }
  };

  // Handle blur
  const handleBlur = (e: React.FocusEvent<HTMLInputElement>) => {
    const { name } = e.target;
    setTouched((prev) => ({ ...prev, [name]: true }));
  };

  // Handle submit
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    // Mark all fields as touched
    setTouched({
      sku: true,
      name: true,
      category: true,
      current_stock: true,
      reorder_threshold: true,
      barcode: true,
      unit_cost: true,
    });

    if (!validateForm()) {
      toast.error('Please fix the errors in the form');
      return;
    }

    if (mode === 'create') {
      const createData: ProductCreate = {
        sku: formData.sku.trim(),
        name: formData.name.trim(),
        category: formData.category.trim(),
        current_stock: parseInt(formData.current_stock),
        reorder_threshold: parseInt(formData.reorder_threshold),
        barcode: formData.barcode.trim() || undefined,
        unit_cost: formData.unit_cost ? parseFloat(formData.unit_cost) : undefined,
      };
      createMutation.mutate(createData);
    } else if (mode === 'edit' && product) {
      const updateData: ProductUpdate = {
        name: formData.name.trim(),
        category: formData.category.trim(),
        current_stock: parseInt(formData.current_stock),
        reorder_threshold: parseInt(formData.reorder_threshold),
        barcode: formData.barcode.trim() || undefined,
        unit_cost: formData.unit_cost ? parseFloat(formData.unit_cost) : undefined,
      };
      updateMutation.mutate({ id: product.id, data: updateData });
    }
  };

  // Handle close
  const handleClose = () => {
    if (createMutation.isPending || updateMutation.isPending) {
      return; // Prevent closing while submitting
    }
    onClose();
  };

  if (!isOpen) return null;

  const isSubmitting = createMutation.isPending || updateMutation.isPending;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={handleClose}
      />

      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative bg-white rounded-lg shadow-xl max-w-2xl w-full">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900">
              {mode === 'create' ? 'Add New Product' : 'Edit Product'}
            </h2>
            <button
              onClick={handleClose}
              disabled={isSubmitting}
              className="text-gray-400 hover:text-gray-600 transition-colors disabled:opacity-50"
            >
              <XMarkIcon className="w-6 h-6" />
            </button>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* SKU */}
              <div>
                <label htmlFor="sku" className="block text-sm font-medium text-gray-700 mb-1">
                  SKU {mode === 'create' && <span className="text-red-500">*</span>}
                </label>
                <input
                  type="text"
                  id="sku"
                  name="sku"
                  value={formData.sku}
                  onChange={handleChange}
                  onBlur={handleBlur}
                  disabled={mode === 'edit' || isSubmitting}
                  className={`w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed ${
                    touched.sku && errors.sku ? 'border-red-500' : 'border-gray-300'
                  }`}
                  placeholder="e.g., PROD-001"
                />
                {touched.sku && errors.sku && (
                  <p className="mt-1 text-sm text-red-600">{errors.sku}</p>
                )}
              </div>

              {/* Name */}
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
                  Product Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  id="name"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  onBlur={handleBlur}
                  disabled={isSubmitting}
                  className={`w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent ${
                    touched.name && errors.name ? 'border-red-500' : 'border-gray-300'
                  }`}
                  placeholder="e.g., Wireless Mouse"
                />
                {touched.name && errors.name && (
                  <p className="mt-1 text-sm text-red-600">{errors.name}</p>
                )}
              </div>

              {/* Category */}
              <div>
                <label htmlFor="category" className="block text-sm font-medium text-gray-700 mb-1">
                  Category <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  id="category"
                  name="category"
                  value={formData.category}
                  onChange={handleChange}
                  onBlur={handleBlur}
                  disabled={isSubmitting}
                  className={`w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent ${
                    touched.category && errors.category ? 'border-red-500' : 'border-gray-300'
                  }`}
                  placeholder="e.g., Electronics"
                />
                {touched.category && errors.category && (
                  <p className="mt-1 text-sm text-red-600">{errors.category}</p>
                )}
              </div>

              {/* Current Stock */}
              <div>
                <label htmlFor="current_stock" className="block text-sm font-medium text-gray-700 mb-1">
                  Current Stock <span className="text-red-500">*</span>
                </label>
                <input
                  type="number"
                  id="current_stock"
                  name="current_stock"
                  value={formData.current_stock}
                  onChange={handleChange}
                  onBlur={handleBlur}
                  disabled={isSubmitting}
                  min="0"
                  step="1"
                  className={`w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent ${
                    touched.current_stock && errors.current_stock ? 'border-red-500' : 'border-gray-300'
                  }`}
                  placeholder="0"
                />
                {touched.current_stock && errors.current_stock && (
                  <p className="mt-1 text-sm text-red-600">{errors.current_stock}</p>
                )}
              </div>

              {/* Reorder Threshold */}
              <div>
                <label htmlFor="reorder_threshold" className="block text-sm font-medium text-gray-700 mb-1">
                  Reorder Threshold <span className="text-red-500">*</span>
                </label>
                <input
                  type="number"
                  id="reorder_threshold"
                  name="reorder_threshold"
                  value={formData.reorder_threshold}
                  onChange={handleChange}
                  onBlur={handleBlur}
                  disabled={isSubmitting}
                  min="0"
                  step="1"
                  className={`w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent ${
                    touched.reorder_threshold && errors.reorder_threshold ? 'border-red-500' : 'border-gray-300'
                  }`}
                  placeholder="10"
                />
                {touched.reorder_threshold && errors.reorder_threshold && (
                  <p className="mt-1 text-sm text-red-600">{errors.reorder_threshold}</p>
                )}
              </div>

              {/* Barcode */}
              <div>
                <label htmlFor="barcode" className="block text-sm font-medium text-gray-700 mb-1">
                  Barcode (Optional)
                </label>
                <input
                  type="text"
                  id="barcode"
                  name="barcode"
                  value={formData.barcode}
                  onChange={handleChange}
                  onBlur={handleBlur}
                  disabled={isSubmitting}
                  className={`w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent ${
                    touched.barcode && errors.barcode ? 'border-red-500' : 'border-gray-300'
                  }`}
                  placeholder="e.g., 123456789012"
                />
                {touched.barcode && errors.barcode && (
                  <p className="mt-1 text-sm text-red-600">{errors.barcode}</p>
                )}
              </div>

              {/* Unit Cost */}
              <div>
                <label htmlFor="unit_cost" className="block text-sm font-medium text-gray-700 mb-1">
                  Unit Cost (Optional)
                </label>
                <input
                  type="number"
                  id="unit_cost"
                  name="unit_cost"
                  value={formData.unit_cost}
                  onChange={handleChange}
                  onBlur={handleBlur}
                  disabled={isSubmitting}
                  min="0"
                  step="0.01"
                  className={`w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent ${
                    touched.unit_cost && errors.unit_cost ? 'border-red-500' : 'border-gray-300'
                  }`}
                  placeholder="0.00"
                />
                {touched.unit_cost && errors.unit_cost && (
                  <p className="mt-1 text-sm text-red-600">{errors.unit_cost}</p>
                )}
              </div>
            </div>

            {/* Vendor Pricing Section (Create mode only) */}
            {mode === 'create' && (
              <div className="mt-6 border-t border-gray-200 pt-6">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="text-sm font-medium text-gray-900">Vendor Pricing (Optional)</h3>
                    <p className="text-xs text-gray-500 mt-1">Add vendor pricing information for this product</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => setShowVendorSection(!showVendorSection)}
                    className="text-sm text-primary-600 hover:text-primary-700 font-medium"
                  >
                    {showVendorSection ? 'Hide' : 'Show'}
                  </button>
                </div>

                {showVendorSection && (
                  <div className="space-y-4">
                    {vendorPrices.map((vp, index) => (
                      <div key={index} className="bg-gray-50 rounded-lg p-4 relative">
                        <button
                          type="button"
                          onClick={() => removeVendorPrice(index)}
                          className="absolute top-2 right-2 text-gray-400 hover:text-red-600 transition-colors"
                        >
                          <TrashIcon className="h-5 w-5" />
                        </button>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div className="md:col-span-2">
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                              Vendor
                            </label>
                            <select
                              value={vp.vendor_id}
                              onChange={(e) => updateVendorPrice(index, 'vendor_id', e.target.value)}
                              disabled={isSubmitting}
                              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                            >
                              <option value="">Select a vendor</option>
                              {vendors?.map((vendor) => (
                                <option key={vendor.id} value={vendor.id}>
                                  {vendor.name}
                                </option>
                              ))}
                            </select>
                          </div>

                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                              Unit Price
                            </label>
                            <input
                              type="number"
                              value={vp.unit_price}
                              onChange={(e) => updateVendorPrice(index, 'unit_price', e.target.value)}
                              disabled={isSubmitting}
                              min="0"
                              step="0.01"
                              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                              placeholder="0.00"
                            />
                          </div>

                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                              Lead Time (days)
                            </label>
                            <input
                              type="number"
                              value={vp.lead_time_days}
                              onChange={(e) => updateVendorPrice(index, 'lead_time_days', e.target.value)}
                              disabled={isSubmitting}
                              min="0"
                              step="1"
                              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                              placeholder="7"
                            />
                          </div>

                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                              Min. Order Quantity
                            </label>
                            <input
                              type="number"
                              value={vp.minimum_order_quantity}
                              onChange={(e) => updateVendorPrice(index, 'minimum_order_quantity', e.target.value)}
                              disabled={isSubmitting}
                              min="1"
                              step="1"
                              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                              placeholder="1"
                            />
                          </div>
                        </div>
                      </div>
                    ))}

                    <button
                      type="button"
                      onClick={addVendorPrice}
                      disabled={isSubmitting || !vendors || vendors.length === 0}
                      className="w-full px-4 py-2 border-2 border-dashed border-gray-300 rounded-md text-gray-600 hover:border-primary-500 hover:text-primary-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                    >
                      <PlusIcon className="h-5 w-5" />
                      Add Vendor Price
                    </button>

                    {(!vendors || vendors.length === 0) && (
                      <p className="text-xs text-gray-500 text-center">
                        No vendors available. Create vendors first to add pricing.
                      </p>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* Footer */}
            <div className="mt-6 flex justify-end gap-3">
              <button
                type="button"
                onClick={handleClose}
                disabled={isSubmitting}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {isSubmitting && (
                  <svg
                    className="animate-spin h-4 w-4 text-white"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                )}
                {mode === 'create' ? 'Create Product' : 'Update Product'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
