/**
 * Example component demonstrating the API integration layer usage
 * This file is for reference only and should not be imported in production code
 */

import { 
  useProducts, 
  useCreateProduct, 
  useUpdateProduct,
  useDeleteProduct,
  useAlerts,
  useAcknowledgeAlert,
  usePrediction,
  useProductVendors,
  useAdjustStock
} from '../hooks';
import type { ProductCreate, ProductUpdate } from '../types';

// Example 1: Fetching and displaying products
export function ProductListExample() {
  const { data: products, isLoading, error, refetch } = useProducts();

  if (isLoading) return <div>Loading products...</div>;
  if (error) return <div>Error loading products</div>;

  return (
    <div>
      <button onClick={() => refetch()}>Refresh</button>
      <ul>
        {products?.map(product => (
          <li key={product.id}>
            {product.name} - Stock: {product.current_stock}
          </li>
        ))}
      </ul>
    </div>
  );
}

// Example 2: Creating a product with mutation
export function CreateProductExample() {
  const createProduct = useCreateProduct();

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    
    const productData: ProductCreate = {
      sku: formData.get('sku') as string,
      name: formData.get('name') as string,
      category: formData.get('category') as string,
      current_stock: parseInt(formData.get('stock') as string),
      reorder_threshold: parseInt(formData.get('threshold') as string),
    };

    try {
      await createProduct.mutateAsync(productData);
      // Success toast is shown automatically
      e.currentTarget.reset();
    } catch (error) {
      // Error toast is shown automatically
      console.error('Failed to create product:', error);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input name="sku" placeholder="SKU" required />
      <input name="name" placeholder="Name" required />
      <input name="category" placeholder="Category" required />
      <input name="stock" type="number" placeholder="Stock" required />
      <input name="threshold" type="number" placeholder="Threshold" required />
      <button type="submit" disabled={createProduct.isPending}>
        {createProduct.isPending ? 'Creating...' : 'Create Product'}
      </button>
    </form>
  );
}

// Example 3: Updating a product
export function UpdateProductExample({ productId }: { productId: string }) {
  const updateProduct = useUpdateProduct();

  const handleUpdate = async () => {
    const updates: ProductUpdate = {
      current_stock: 50,
      reorder_threshold: 10,
    };

    await updateProduct.mutateAsync({ id: productId, data: updates });
  };

  return (
    <button onClick={handleUpdate} disabled={updateProduct.isPending}>
      Update Stock
    </button>
  );
}

// Example 4: Deleting a product
export function DeleteProductExample({ productId }: { productId: string }) {
  const deleteProduct = useDeleteProduct();

  const handleDelete = async () => {
    if (confirm('Are you sure you want to delete this product?')) {
      await deleteProduct.mutateAsync(productId);
    }
  };

  return (
    <button onClick={handleDelete} disabled={deleteProduct.isPending}>
      Delete
    </button>
  );
}

// Example 5: Fetching with filters
export function FilteredProductsExample() {
  const { data: products } = useProducts({ 
    category: 'Electronics',
    search: 'laptop',
    limit: 10 
  });

  return (
    <div>
      {products?.map(product => (
        <div key={product.id}>{product.name}</div>
      ))}
    </div>
  );
}

// Example 6: Managing alerts
export function AlertsExample() {
  const { data: alerts, isLoading } = useAlerts();
  const acknowledgeAlert = useAcknowledgeAlert();

  if (isLoading) return <div>Loading alerts...</div>;

  return (
    <div>
      {alerts?.map(alert => (
        <div key={alert.id}>
          <p>{alert.message}</p>
          <button 
            onClick={() => acknowledgeAlert.mutate(alert.id)}
            disabled={alert.status !== 'active'}
          >
            Acknowledge
          </button>
        </div>
      ))}
    </div>
  );
}

// Example 7: Fetching related data in parallel
export function ProductDetailExample({ productId }: { productId: string }) {
  // All these queries run in parallel
  const { data: prediction } = usePrediction(productId);
  const { data: vendors } = useProductVendors(productId);

  return (
    <div>
      <h2>Prediction</h2>
      <p>Depletion Date: {prediction?.predicted_depletion_date || 'N/A'}</p>
      <p>Confidence: {prediction?.confidence_score || 'N/A'}</p>

      <h2>Vendors</h2>
      <ul>
        {vendors?.map(vendor => (
          <li key={vendor.id}>
            {vendor.vendor_name} - ${vendor.unit_price}
            {vendor.is_recommended && ' (Recommended)'}
          </li>
        ))}
      </ul>
    </div>
  );
}

// Example 8: Stock adjustment
export function StockAdjustmentExample({ productId }: { productId: string }) {
  const adjustStock = useAdjustStock();

  const handleAdjust = async (quantity: number) => {
    await adjustStock.mutateAsync({
      product_id: productId,
      quantity,
      reason: 'Manual adjustment',
    });
  };

  return (
    <div>
      <button onClick={() => handleAdjust(10)}>Add 10</button>
      <button onClick={() => handleAdjust(-10)}>Remove 10</button>
    </div>
  );
}

// Example 9: Conditional fetching
export function ConditionalFetchExample({ shouldFetch, productId }: { 
  shouldFetch: boolean; 
  productId: string;
}) {
  // Only fetch when shouldFetch is true
  const { data: prediction } = usePrediction(productId, 90, shouldFetch);

  return (
    <div>
      {prediction ? (
        <p>Depletion: {prediction.predicted_depletion_date}</p>
      ) : (
        <p>No prediction available</p>
      )}
    </div>
  );
}

// Example 10: Handling loading and error states
export function CompleteExample() {
  const { 
    data: products, 
    isLoading, 
    isError, 
    error,
    refetch,
    isFetching 
  } = useProducts();

  if (isLoading) {
    return <div>Loading products...</div>;
  }

  if (isError) {
    return (
      <div>
        <p>Error: {error.message}</p>
        <button onClick={() => refetch()}>Try Again</button>
      </div>
    );
  }

  return (
    <div>
      <button onClick={() => refetch()} disabled={isFetching}>
        {isFetching ? 'Refreshing...' : 'Refresh'}
      </button>
      <ul>
        {products?.map(product => (
          <li key={product.id}>{product.name}</li>
        ))}
      </ul>
    </div>
  );
}
