import toast from 'react-hot-toast';
import { AxiosError } from 'axios';

export interface ApiError {
  message: string;
  code?: string;
  status?: number;
  details?: any;
}

/**
 * Extract error message from various error types
 */
export function getErrorMessage(error: unknown): string {
  if (typeof error === 'string') {
    return error;
  }

  if (error instanceof AxiosError) {
    // Handle Axios errors
    if (error.response) {
      const data = error.response.data;
      return data?.detail || data?.message || `Error: ${error.response.status}`;
    }
    if (error.request) {
      return 'Network error. Please check your connection.';
    }
    return error.message || 'An unexpected error occurred';
  }

  if (error instanceof Error) {
    return error.message;
  }

  return 'An unexpected error occurred';
}

/**
 * Parse API error into structured format
 */
export function parseApiError(error: unknown): ApiError {
  if (error instanceof AxiosError) {
    return {
      message: getErrorMessage(error),
      code: error.code,
      status: error.response?.status,
      details: error.response?.data,
    };
  }

  return {
    message: getErrorMessage(error),
  };
}

/**
 * Show error toast notification
 */
export function showErrorToast(error: unknown, fallbackMessage?: string): void {
  const message = getErrorMessage(error);
  toast.error(fallbackMessage || message);
}

/**
 * Show success toast notification
 */
export function showSuccessToast(message: string): void {
  toast.success(message);
}

/**
 * Handle API errors with automatic toast notifications
 */
export function handleApiError(error: unknown, customMessage?: string): void {
  const apiError = parseApiError(error);
  
  // Log error in development
  if (import.meta.env.DEV) {
    console.error('API Error:', apiError);
  }

  // Show toast notification
  showErrorToast(error, customMessage);
}

/**
 * Retry function with exponential backoff
 */
export async function retryWithBackoff<T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  baseDelay: number = 1000
): Promise<T> {
  let lastError: unknown;

  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;
      
      if (i < maxRetries - 1) {
        const delay = baseDelay * Math.pow(2, i);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }

  throw lastError;
}

/**
 * Check if error is a network error
 */
export function isNetworkError(error: unknown): boolean {
  if (error instanceof AxiosError) {
    return !error.response && !!error.request;
  }
  return false;
}

/**
 * Check if error is an authentication error
 */
export function isAuthError(error: unknown): boolean {
  if (error instanceof AxiosError) {
    return error.response?.status === 401;
  }
  return false;
}

/**
 * Check if error is a validation error
 */
export function isValidationError(error: unknown): boolean {
  if (error instanceof AxiosError) {
    return error.response?.status === 422 || error.response?.status === 400;
  }
  return false;
}
