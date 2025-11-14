import { describe, it, expect } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useDebounce } from '../useDebounce';

describe('useDebounce', () => {
  it('returns initial value immediately', () => {
    const { result } = renderHook(() => useDebounce('initial', 300));
    expect(result.current).toBe('initial');
  });

  it('debounces value changes', async () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      {
        initialProps: { value: 'initial', delay: 100 },
      }
    );

    expect(result.current).toBe('initial');

    // Update the value
    rerender({ value: 'updated', delay: 100 });

    // Value should not change immediately
    expect(result.current).toBe('initial');

    // Wait for the debounced value to update
    await waitFor(
      () => {
        expect(result.current).toBe('updated');
      },
      { timeout: 200 }
    );
  });

  it('cancels previous timeout on rapid changes', async () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      {
        initialProps: { value: 'initial', delay: 100 },
      }
    );

    // Rapid updates
    rerender({ value: 'first', delay: 100 });
    rerender({ value: 'second', delay: 100 });
    rerender({ value: 'third', delay: 100 });

    // Value should still be initial
    expect(result.current).toBe('initial');

    // Wait for the final debounced value
    await waitFor(
      () => {
        expect(result.current).toBe('third');
      },
      { timeout: 200 }
    );
  });

  it('uses custom delay', async () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      {
        initialProps: { value: 'initial', delay: 150 },
      }
    );

    rerender({ value: 'updated', delay: 150 });

    // Should still be initial shortly after
    expect(result.current).toBe('initial');

    // Should update after delay
    await waitFor(
      () => {
        expect(result.current).toBe('updated');
      },
      { timeout: 250 }
    );
  });

  it('works with different value types', async () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      {
        initialProps: { value: 0, delay: 100 },
      }
    );

    expect(result.current).toBe(0);

    rerender({ value: 42, delay: 100 });

    await waitFor(
      () => {
        expect(result.current).toBe(42);
      },
      { timeout: 200 }
    );
  });
});
