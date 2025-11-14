import { useState, useCallback } from 'react';
import { handleApiError, showSuccessToast } from '../utils/errorHandling';

interface UseAsyncOperationOptions {
  onSuccess?: (data?: any) => void;
  onError?: (error: unknown) => void;
  successMessage?: string;
  errorMessage?: string;
}

interface UseAsyncOperationResult<T> {
  execute: (...args: any[]) => Promise<T | undefined>;
  isLoading: boolean;
  error: unknown | null;
  data: T | null;
  reset: () => void;
}

/**
 * Custom hook for handling async operations with loading and error states
 */
export function useAsyncOperation<T = any>(
  asyncFn: (...args: any[]) => Promise<T>,
  options: UseAsyncOperationOptions = {}
): UseAsyncOperationResult<T> {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<unknown | null>(null);
  const [data, setData] = useState<T | null>(null);

  const execute = useCallback(
    async (...args: any[]): Promise<T | undefined> => {
      setIsLoading(true);
      setError(null);

      try {
        const result = await asyncFn(...args);
        setData(result);

        if (options.successMessage) {
          showSuccessToast(options.successMessage);
        }

        if (options.onSuccess) {
          options.onSuccess(result);
        }

        return result;
      } catch (err) {
        setError(err);

        if (options.errorMessage) {
          handleApiError(err, options.errorMessage);
        } else {
          handleApiError(err);
        }

        if (options.onError) {
          options.onError(err);
        }

        return undefined;
      } finally {
        setIsLoading(false);
      }
    },
    [asyncFn, options]
  );

  const reset = useCallback(() => {
    setIsLoading(false);
    setError(null);
    setData(null);
  }, []);

  return {
    execute,
    isLoading,
    error,
    data,
    reset,
  };
}
