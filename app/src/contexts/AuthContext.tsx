/**
 * 认证上下文
 * 
 * 提供全局的认证状态管理，确保整个应用共享同一个认证状态
 */

import React, { createContext, useContext, ReactNode } from 'react';
import useAuth from '../store/slices/authSlice';

/**
 * 认证上下文类型
 */
type AuthContextType = ReturnType<typeof useAuth>;

/**
 * 创建认证上下文
 */
const AuthContext = createContext<AuthContextType | undefined>(undefined);

/**
 * 认证提供者属性
 */
interface AuthProviderProps {
  children: ReactNode;
}

/**
 * 认证提供者组件
 * 
 * 在应用的最顶层使用，确保所有组件共享同一个认证状态
 */
export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const auth = useAuth();

  return (
    <AuthContext.Provider value={auth}>
      {children}
    </AuthContext.Provider>
  );
};

/**
 * 使用认证上下文的Hook
 * 
 * 在任何组件中使用此Hook来访问认证状态和方法
 */
export const useAuthContext = (): AuthContextType => {
  const context = useContext(AuthContext);
  
  if (context === undefined) {
    throw new Error('useAuthContext must be used within an AuthProvider');
  }
  
  return context;
};

export default AuthProvider;
