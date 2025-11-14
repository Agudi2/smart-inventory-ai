import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { useAuthStore } from '../authStore';

describe('authStore', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear();
    // Reset store state
    useAuthStore.setState({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
    });
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('initializes with null user and not authenticated', () => {
    const state = useAuthStore.getState();
    expect(state.user).toBeNull();
    expect(state.accessToken).toBeNull();
    expect(state.refreshToken).toBeNull();
    expect(state.isAuthenticated).toBe(false);
  });

  it('sets authentication state correctly', () => {
    const mockUser = {
      id: '1',
      email: 'test@example.com',
      full_name: 'Test User',
      role: 'user',
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    };
    const mockAccessToken = 'access-token-123';
    const mockRefreshToken = 'refresh-token-456';

    useAuthStore.getState().setAuth(mockUser, mockAccessToken, mockRefreshToken);

    const state = useAuthStore.getState();
    expect(state.user).toEqual(mockUser);
    expect(state.accessToken).toBe(mockAccessToken);
    expect(state.refreshToken).toBe(mockRefreshToken);
    expect(state.isAuthenticated).toBe(true);
  });

  it('stores tokens in localStorage when setting auth', () => {
    const mockUser = {
      id: '1',
      email: 'test@example.com',
      full_name: 'Test User',
      role: 'user',
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    };
    const mockAccessToken = 'access-token-123';
    const mockRefreshToken = 'refresh-token-456';

    useAuthStore.getState().setAuth(mockUser, mockAccessToken, mockRefreshToken);

    expect(localStorage.getItem('access_token')).toBe(mockAccessToken);
    expect(localStorage.getItem('refresh_token')).toBe(mockRefreshToken);
  });

  it('clears authentication state correctly', () => {
    const mockUser = {
      id: '1',
      email: 'test@example.com',
      full_name: 'Test User',
      role: 'user',
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    };

    useAuthStore.getState().setAuth(mockUser, 'token1', 'token2');
    useAuthStore.getState().clearAuth();

    const state = useAuthStore.getState();
    expect(state.user).toBeNull();
    expect(state.accessToken).toBeNull();
    expect(state.refreshToken).toBeNull();
    expect(state.isAuthenticated).toBe(false);
  });

  it('removes tokens from localStorage when clearing auth', () => {
    const mockUser = {
      id: '1',
      email: 'test@example.com',
      full_name: 'Test User',
      role: 'user',
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    };

    useAuthStore.getState().setAuth(mockUser, 'token1', 'token2');
    useAuthStore.getState().clearAuth();

    expect(localStorage.getItem('access_token')).toBeNull();
    expect(localStorage.getItem('refresh_token')).toBeNull();
  });

  it('updates user information', () => {
    const initialUser = {
      id: '1',
      email: 'test@example.com',
      full_name: 'Test User',
      role: 'user',
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    };

    const updatedUser = {
      ...initialUser,
      full_name: 'Updated User',
    };

    useAuthStore.getState().setAuth(initialUser, 'token1', 'token2');
    useAuthStore.getState().updateUser(updatedUser);

    const state = useAuthStore.getState();
    expect(state.user?.full_name).toBe('Updated User');
    expect(state.isAuthenticated).toBe(true);
  });
});
