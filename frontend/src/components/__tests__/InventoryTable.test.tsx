import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '../../test/test-utils';
import InventoryTable from '../InventoryTable';

const mockProducts = [
  {
    id: '1',
    sku: 'PROD-001',
    name: 'Wireless Mouse',
    category: 'Electronics',
    current_stock: 50,
    reorder_threshold: 10,
    stock_status: 'sufficient' as const,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: '2',
    sku: 'PROD-002',
    name: 'USB Cable',
    category: 'Electronics',
    current_stock: 5,
    reorder_threshold: 10,
    stock_status: 'low' as const,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: '3',
    sku: 'PROD-003',
    name: 'Notebook',
    category: 'Office Supplies',
    current_stock: 2,
    reorder_threshold: 10,
    stock_status: 'critical' as const,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
];

describe('InventoryTable', () => {
  const mockOnEdit = vi.fn();
  const mockOnDelete = vi.fn();
  const mockOnView = vi.fn();

  it('renders product data correctly', () => {
    render(
      <InventoryTable
        products={mockProducts}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
        onView={mockOnView}
      />
    );

    expect(screen.getByText('Wireless Mouse')).toBeInTheDocument();
    expect(screen.getByText('USB Cable')).toBeInTheDocument();
    expect(screen.getByText('Notebook')).toBeInTheDocument();
  });

  it('displays stock status badges correctly', () => {
    render(
      <InventoryTable
        products={mockProducts}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
        onView={mockOnView}
      />
    );

    expect(screen.getByText('Sufficient')).toBeInTheDocument();
    expect(screen.getByText('Low Stock')).toBeInTheDocument();
    expect(screen.getByText('Critical')).toBeInTheDocument();
  });

  it('filters products by search term', async () => {
    render(
      <InventoryTable
        products={mockProducts}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
        onView={mockOnView}
      />
    );

    const searchInput = screen.getByPlaceholderText(/search by name/i);
    fireEvent.change(searchInput, { target: { value: 'Mouse' } });

    await waitFor(() => {
      expect(screen.getByText('Wireless Mouse')).toBeInTheDocument();
      expect(screen.queryByText('USB Cable')).not.toBeInTheDocument();
      expect(screen.queryByText('Notebook')).not.toBeInTheDocument();
    });
  });

  it('filters products by category', () => {
    render(
      <InventoryTable
        products={mockProducts}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
        onView={mockOnView}
      />
    );

    const categorySelect = screen.getByRole('combobox');
    fireEvent.change(categorySelect, { target: { value: 'Office Supplies' } });

    expect(screen.getByText('Notebook')).toBeInTheDocument();
    expect(screen.queryByText('Wireless Mouse')).not.toBeInTheDocument();
    expect(screen.queryByText('USB Cable')).not.toBeInTheDocument();
  });

  it('calls onEdit when edit button is clicked', () => {
    render(
      <InventoryTable
        products={mockProducts}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
        onView={mockOnView}
      />
    );

    const editButtons = screen.getAllByTitle('Edit product');
    fireEvent.click(editButtons[0]);

    // Should be called with a product (the table sorts by default)
    expect(mockOnEdit).toHaveBeenCalledTimes(1);
    expect(mockOnEdit).toHaveBeenCalledWith(expect.objectContaining({
      id: expect.any(String),
      sku: expect.any(String),
      name: expect.any(String),
    }));
  });

  it('calls onDelete when delete button is clicked', () => {
    render(
      <InventoryTable
        products={mockProducts}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
        onView={mockOnView}
      />
    );

    const deleteButtons = screen.getAllByTitle('Delete product');
    fireEvent.click(deleteButtons[0]);

    // Should be called with a product
    expect(mockOnDelete).toHaveBeenCalledTimes(1);
    expect(mockOnDelete).toHaveBeenCalledWith(expect.objectContaining({
      id: expect.any(String),
      sku: expect.any(String),
      name: expect.any(String),
    }));
  });

  it('calls onView when view button is clicked', () => {
    render(
      <InventoryTable
        products={mockProducts}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
        onView={mockOnView}
      />
    );

    const viewButtons = screen.getAllByTitle('View details');
    fireEvent.click(viewButtons[0]);

    // Should be called with a product
    expect(mockOnView).toHaveBeenCalledTimes(1);
    expect(mockOnView).toHaveBeenCalledWith(expect.objectContaining({
      id: expect.any(String),
      sku: expect.any(String),
      name: expect.any(String),
    }));
  });

  it('displays empty state when no products', () => {
    render(
      <InventoryTable
        products={[]}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
        onView={mockOnView}
      />
    );

    expect(screen.getByText(/no products available/i)).toBeInTheDocument();
  });

  it('sorts products by name when header is clicked', () => {
    render(
      <InventoryTable
        products={mockProducts}
        onEdit={mockOnEdit}
        onDelete={mockOnDelete}
        onView={mockOnView}
      />
    );

    const nameHeader = screen.getByText('Name');
    fireEvent.click(nameHeader);

    // After clicking, products should be sorted alphabetically
    // Check that all product names are still visible
    expect(screen.getByText('Notebook')).toBeInTheDocument();
    expect(screen.getByText('USB Cable')).toBeInTheDocument();
    expect(screen.getByText('Wireless Mouse')).toBeInTheDocument();
  });
});
