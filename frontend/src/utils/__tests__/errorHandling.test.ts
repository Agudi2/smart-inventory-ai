import { describe, it, expect } from 'vitest';
import { AxiosError } from 'axios';
import {
  getErrorMessage,
  parseApiError,
  isNetworkError,
  isAuthError,
  isValidationError,
} from '../errorHandling';

// Helper to create proper AxiosError instances
function createAxiosError(config: {
  response?: any;
  request?: any;
  message?: string;
  code?: string;
}): AxiosError {
  const error = new AxiosError(
    config.message || 'Error',
    config.code,
    undefined,
    config.request,
    config.response
  );
  return error;
}

describe('errorHandling', () => {
  describe('getErrorMessage', () => {
    it('returns string error as is', () => {
      const result = getErrorMessage('Simple error message');
      expect(result).toBe('Simple error message');
    });

    it('extracts message from Error object', () => {
      const error = new Error('Error object message');
      const result = getErrorMessage(error);
      expect(result).toBe('Error object message');
    });

    it('extracts detail from Axios error response', () => {
      const axiosError = createAxiosError({
        response: {
          data: { detail: 'API error detail' },
          status: 400,
          statusText: 'Bad Request',
          headers: {},
          config: {} as any,
        },
      });

      const result = getErrorMessage(axiosError);
      expect(result).toBe('API error detail');
    });

    it('returns network error message for request without response', () => {
      const axiosError = createAxiosError({
        request: {},
        message: 'Network Error',
      });

      const result = getErrorMessage(axiosError);
      expect(result).toBe('Network error. Please check your connection.');
    });

    it('returns default message for unknown error types', () => {
      const result = getErrorMessage({ unknown: 'error' });
      expect(result).toBe('An unexpected error occurred');
    });
  });

  describe('parseApiError', () => {
    it('parses Axios error correctly', () => {
      const axiosError = createAxiosError({
        code: 'ERR_BAD_REQUEST',
        response: {
          data: { detail: 'Validation failed' },
          status: 422,
          statusText: 'Unprocessable Entity',
          headers: {},
          config: {} as any,
        },
      });

      const result = parseApiError(axiosError);

      expect(result.message).toBe('Validation failed');
      expect(result.code).toBe('ERR_BAD_REQUEST');
      expect(result.status).toBe(422);
      expect(result.details).toEqual({ detail: 'Validation failed' });
    });

    it('parses non-Axios error', () => {
      const error = new Error('Generic error');
      const result = parseApiError(error);

      expect(result.message).toBe('Generic error');
      expect(result.code).toBeUndefined();
      expect(result.status).toBeUndefined();
    });
  });

  describe('isNetworkError', () => {
    it('returns true for network errors', () => {
      const axiosError = createAxiosError({
        request: {},
        message: 'Network Error',
      });

      expect(isNetworkError(axiosError)).toBe(true);
    });

    it('returns false for response errors', () => {
      const axiosError = createAxiosError({
        response: {
          data: {},
          status: 500,
          statusText: 'Internal Server Error',
          headers: {},
          config: {} as any,
        },
      });

      expect(isNetworkError(axiosError)).toBe(false);
    });

    it('returns false for non-Axios errors', () => {
      expect(isNetworkError(new Error('Generic error'))).toBe(false);
    });
  });

  describe('isAuthError', () => {
    it('returns true for 401 errors', () => {
      const axiosError = createAxiosError({
        response: {
          data: {},
          status: 401,
          statusText: 'Unauthorized',
          headers: {},
          config: {} as any,
        },
      });

      expect(isAuthError(axiosError)).toBe(true);
    });

    it('returns false for non-401 errors', () => {
      const axiosError = createAxiosError({
        response: {
          data: {},
          status: 404,
          statusText: 'Not Found',
          headers: {},
          config: {} as any,
        },
      });

      expect(isAuthError(axiosError)).toBe(false);
    });
  });

  describe('isValidationError', () => {
    it('returns true for 422 errors', () => {
      const axiosError = createAxiosError({
        response: {
          data: {},
          status: 422,
          statusText: 'Unprocessable Entity',
          headers: {},
          config: {} as any,
        },
      });

      expect(isValidationError(axiosError)).toBe(true);
    });

    it('returns true for 400 errors', () => {
      const axiosError = createAxiosError({
        response: {
          data: {},
          status: 400,
          statusText: 'Bad Request',
          headers: {},
          config: {} as any,
        },
      });

      expect(isValidationError(axiosError)).toBe(true);
    });

    it('returns false for other status codes', () => {
      const axiosError = createAxiosError({
        response: {
          data: {},
          status: 500,
          statusText: 'Internal Server Error',
          headers: {},
          config: {} as any,
        },
      });

      expect(isValidationError(axiosError)).toBe(false);
    });
  });
});
