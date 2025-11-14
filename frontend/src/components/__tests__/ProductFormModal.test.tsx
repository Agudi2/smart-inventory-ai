import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '../../test/test-utils';
import ProductFormModal from '../ProductFormModal';

describe('ProductFormModal', () => {
  const mockOnClose = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('does not render when isOpen is false', () => {
    render(
      <ProductFormModal
        isOpen={false}
        onClose={mockOnClose}
        mode="create"
      />
    );

    expect(screen.queryByText('Add New Product')).not.toBeInTheDocument();
  });

  it('renders create form when mode is create', () => {
    render(
      <ProductFormModal
        isOpen={true}
        onClose={mockOnClose}
        mode="create"
      />
    );

    expect(screen.getByText('Add New Product')).toBeInTheDocument();
    expect(screen.getByLabelText(/sku/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/product name/i)).toBeInTheDocument();
  });

  it('renders edit form when mode is edit', () => {
    const mockProduct = {
      id: '1',
      sku: 'PROD-001',
      name: 'Test Product',
      category: 'Electronics',
      current_stock: 50,
      reorder_threshold: 10,
      stock_status: 'sufficient' as const,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    };

    render(
      <ProductFormModal
        isOpen={true}
        onClose={mockOnClose}
        mode="edit"
        product={mockProduct}
      />
    );

    expect(screen.getByText('Edit Product')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Test Product')).toBeInTheDocument();
  });

  it('validates required fields', async () => {
    render(
      <ProductFormModal
        isOpen={true}
        onClose={mockOnClose}
        mode="create"
      />
    );

    const submitButton = screen.getByRole('button', { name: /create product/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('SKU is required')).toBeInTheDocument();
      expect(screen.getByText('Product name is required')).toBeInTheDocument();
      expect(screen.getByText('Category is required')).toBeInTheDocument();
    });
  });

  it('accepts valid form input', () => {
    render(
      <ProductFormModal
        isOpen={true}
        onClose={mockOnClose}
        mode="create"
      />
    );

    const skuInput = screen.getByLabelText(/sku/i);
    const nameInput = screen.getByLabelText(/product name/i);
    const categoryInput = screen.getByLabelText(/category/i);
    const currentStockInput = screen.getByLabelText(/current stock/i);

    // Fill with valid data
    fireEvent.change(skuInput, { target: { value: 'TEST-001' } });
    fireEvent.change(nameInput, { target: { value: 'Test Product' } });
    fireEvent.change(categoryInput, { target: { value: 'Test' } });
    fireEvent.change(currentStockInput, { target: { value: '100' } });

    // All inputs should have the correct values
    expect(skuInput).toHaveValue('TEST-001');
    expect(nameInput).toHaveValue('Test Product');
    expect(categoryInput).toHaveValue('Test');
    expect(currentStockInput).toHaveValue(100);
  });

  it('clears errors when user starts typing', async () => {
    render(
      <ProductFormModal
        isOpen={true}
        onClose={mockOnClose}
        mode="create"
      />
    );

    const submitButton = screen.getByRole('button', { name: /create product/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Product name is required')).toBeInTheDocument();
    });

    const nameInput = screen.getByLabelText(/product name/i);
    fireEvent.change(nameInput, { target: { value: 'New Product' } });

    // Error should be cleared
    expect(screen.queryByText('Product name is required')).not.toBeInTheDocument();
  });

  it('disables SKU field in edit mode', () => {
    const mockProduct = {
      id: '1',
      sku: 'PROD-001',
      name: 'Test Product',
      category: 'Electronics',
      current_stock: 50,
      reorder_threshold: 10,
      stock_status: 'sufficient' as const,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    };

    render(
      <ProductFormModal
        isOpen={true}
        onClose={mockOnClose}
        mode="edit"
        product={mockProduct}
      />
    );

    const skuInput = screen.getByLabelText(/sku/i);
    expect(skuInput).toBeDisabled();
  });

  it('calls onClose when cancel button is clicked', () => {
    render(
      <ProductFormModal
        isOpen={true}
        onClose={mockOnClose}
        mode="create"
      />
    );

    const cancelButton = screen.getByRole('button', { name: /cancel/i });
    fireEvent.click(cancelButton);

    expect(mockOnClose).toHaveBeenCalled();
  });

  it('handles optional fields correctly', () => {
    render(
      <ProductFormModal
        isOpen={true}
        onClose={mockOnClose}
        mode="create"
      />
    );

    const barcodeInput = screen.getByLabelText(/barcode/i);
    const unitCostInput = screen.getByLabelText(/unit cost/i);

    // Optional fields should be empty initially
    expect(barcodeInput).toHaveValue('');
    expect(unitCostInput).toHaveValue(null);

    // Should accept values
    fireEvent.change(barcodeInput, { target: { value: '123456' } });
    fireEvent.change(unitCostInput, { target: { value: '19.99' } });

    expect(barcodeInput).toHaveValue('123456');
    expect(unitCostInput).toHaveValue(19.99);
  });
});
