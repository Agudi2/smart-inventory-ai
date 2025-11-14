import { describe, it, expect, vi, beforeEach } from 'vitest';
import { productService } from '../productService';
import api from '../api';

vi.mock('../api');

describe('productService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getProducts', () => {
    it('fetches all products without filters', async () => {
      const mockProducts = [
        {
          id: '1',
          sku: 'PROD-001',
          name: 'Product 1',
          category: 'Electronics',
          current_stock: 50,
          reorder_threshold: 10,
          stock_status: 'sufficient' as const,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
      ];

      vi.mocked(api.get).mockResolvedValue({ data: mockProducts });

      const result = await productService.getProducts();

      expect(api.get).toHaveBeenCalledWith('/products?');
      expect(result).toEqual(mockProducts);
    });

    it('fetches products with category filter', async () => {
      const mockProducts = [
        {
          id: '1',
          sku: 'PROD-001',
          name: 'Product 1',
          category: 'Electronics',
          current_stock: 50,
          reorder_threshold: 10,
          stock_status: 'sufficient' as const,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
      ];

      vi.mocked(api.get).mockResolvedValue({ data: mockProducts });

      await productService.getProducts({ category: 'Electronics' });

      expect(api.get).toHaveBeenCalledWith('/products?category=Electronics');
    });

    it('fetches products with search filter', async () => {
      vi.mocked(api.get).mockResolvedValue({ data: [] });

      await productService.getProducts({ search: 'mouse' });

      expect(api.get).toHaveBeenCalledWith('/products?search=mouse');
    });
  });

  describe('getProduct', () => {
    it('fetches a single product by id', async () => {
      const mockProduct = {
        id: '1',
        sku: 'PROD-001',
        name: 'Product 1',
        category: 'Electronics',
        current_stock: 50,
        reorder_threshold: 10,
        stock_status: 'sufficient' as const,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      };

      vi.mocked(api.get).mockResolvedValue({ data: mockProduct });

      const result = await productService.getProduct('1');

      expect(api.get).toHaveBeenCalledWith('/products/1');
      expect(result).toEqual(mockProduct);
    });
  });

  describe('createProduct', () => {
    it('creates a new product', async () => {
      const newProduct = {
        sku: 'PROD-002',
        name: 'New Product',
        category: 'Electronics',
        current_stock: 100,
        reorder_threshold: 20,
      };

      const createdProduct = {
        id: '2',
        ...newProduct,
        stock_status: 'sufficient' as const,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      };

      vi.mocked(api.post).mockResolvedValue({ data: createdProduct });

      const result = await productService.createProduct(newProduct);

      expect(api.post).toHaveBeenCalledWith('/products', newProduct);
      expect(result).toEqual(createdProduct);
    });
  });

  describe('updateProduct', () => {
    it('updates an existing product', async () => {
      const updateData = {
        name: 'Updated Product',
        current_stock: 75,
      };

      const updatedProduct = {
        id: '1',
        sku: 'PROD-001',
        name: 'Updated Product',
        category: 'Electronics',
        current_stock: 75,
        reorder_threshold: 10,
        stock_status: 'sufficient' as const,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-02T00:00:00Z',
      };

      vi.mocked(api.put).mockResolvedValue({ data: updatedProduct });

      const result = await productService.updateProduct('1', updateData);

      expect(api.put).toHaveBeenCalledWith('/products/1', updateData);
      expect(result).toEqual(updatedProduct);
    });
  });

  describe('deleteProduct', () => {
    it('deletes a product', async () => {
      vi.mocked(api.delete).mockResolvedValue({ data: undefined });

      await productService.deleteProduct('1');

      expect(api.delete).toHaveBeenCalledWith('/products/1');
    });
  });
});
