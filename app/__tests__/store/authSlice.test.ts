/**
 * 认证状态管理测试
 */

import { renderHook, act } from '@testing-library/react-hooks';
import { useAuth } from '../../src/store/slices/authSlice';

// Mock setTimeout for testing
jest.useFakeTimers();

describe('useAuth Hook', () => {
  beforeEach(() => {
    jest.clearAllTimers();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  it('should have initial state', () => {
    const { result } = renderHook(() => useAuth());
    
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBe(null);
    expect(result.current.token).toBe(null);
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBe(null);
  });

  it('should login successfully with correct credentials', async () => {
    const { result } = renderHook(() => useAuth());
    
    let loginResult;
    
    await act(async () => {
      const loginPromise = result.current.login('learner@example.com', '123456');
      
      // Fast-forward timers to resolve the promise
      jest.advanceTimersByTime(1000);
      
      loginResult = await loginPromise;
    });
    
    expect(loginResult.success).toBe(true);
    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.user).toBeTruthy();
    expect(result.current.token).toBeTruthy();
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBe(null);
  });

  it('should fail login with incorrect credentials', async () => {
    const { result } = renderHook(() => useAuth());
    
    let loginResult;
    
    await act(async () => {
      const loginPromise = result.current.login('wrong@email.com', 'wrongpassword');
      
      // Fast-forward timers to resolve the promise
      jest.advanceTimersByTime(1000);
      
      loginResult = await loginPromise;
    });
    
    expect(loginResult.success).toBe(false);
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBe(null);
    expect(result.current.token).toBe(null);
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeTruthy();
  });

  it('should register successfully', async () => {
    const { result } = renderHook(() => useAuth());
    
    const userData = {
      email: 'newuser@example.com',
      username: 'newuser',
      password: 'password123',
      firstName: 'New',
      lastName: 'User',
    };
    
    let registerResult;
    
    await act(async () => {
      const registerPromise = result.current.register(userData);
      
      // Fast-forward timers to resolve the promise
      jest.advanceTimersByTime(1500);
      
      registerResult = await registerPromise;
    });
    
    expect(registerResult.success).toBe(true);
    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.user).toBeTruthy();
    expect(result.current.user?.email).toBe(userData.email);
    expect(result.current.token).toBeTruthy();
  });

  it('should logout successfully', async () => {
    const { result } = renderHook(() => useAuth());
    
    // First login
    await act(async () => {
      const loginPromise = result.current.login('learner@example.com', '123456');
      jest.advanceTimersByTime(1000);
      await loginPromise;
    });
    
    // Then logout
    await act(async () => {
      const logoutPromise = result.current.logout();
      jest.advanceTimersByTime(500);
      await logoutPromise;
    });
    
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBe(null);
    expect(result.current.token).toBe(null);
  });

  it('should clear error', () => {
    const { result } = renderHook(() => useAuth());
    
    act(() => {
      result.current.clearError();
    });
    
    expect(result.current.error).toBe(null);
  });

  it('should update user successfully', async () => {
    const { result } = renderHook(() => useAuth());
    
    // First login
    await act(async () => {
      const loginPromise = result.current.login('learner@example.com', '123456');
      jest.advanceTimersByTime(1000);
      await loginPromise;
    });
    
    // Then update user
    const updateData = { firstName: 'Updated', lastName: 'Name' };
    
    await act(async () => {
      const updatePromise = result.current.updateUser(updateData);
      jest.advanceTimersByTime(800);
      await updatePromise;
    });
    
    expect(result.current.user?.firstName).toBe('Updated');
    expect(result.current.user?.lastName).toBe('Name');
  });
});
