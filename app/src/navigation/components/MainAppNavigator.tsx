/**
 * 主应用导航器
 * 
 * 根据用户登录状态显示不同的界面：
 * - 未登录：显示认证界面（登录/注册）
 * - 已登录：显示主应用界面（Tab导航）
 */

import React, { useEffect, useState } from 'react';
import {
  View,
  StyleSheet,
  ActivityIndicator,
  Text,
  TouchableOpacity,
} from 'react-native';
import { useTheme } from '../../contexts/ThemeContext';
import { useAuthContext } from '../../contexts/AuthContext';
import AuthNavigator from './AuthNavigator';
import SimpleAppNavigator from './SimpleAppNavigator';

/**
 * 主应用导航器组件
 */
export const MainAppNavigator: React.FC = () => {
  const { theme } = useTheme();
  const authData = useAuthContext();
  const { isAuthenticated, loading, checkAuth, login } = authData;
  const [isInitializing, setIsInitializing] = useState(true);

  // 详细的状态监控
  console.log('MainAppNavigator 完整状态:', authData);

  // 应用启动时检查认证状态
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        await checkAuth();
      } catch (error) {
        console.error('Auth initialization error:', error);
      } finally {
        setIsInitializing(false);
      }
    };

    initializeAuth();
  }, [checkAuth]);

  // 处理认证成功
  const handleAuthSuccess = () => {
    // 认证成功后，useAuth hook会自动更新isAuthenticated状态
    // 这里可以添加额外的逻辑，比如导航到特定页面
    console.log('用户认证成功');
  };

  // 添加调试信息
  console.log('MainAppNavigator - isAuthenticated:', isAuthenticated, 'loading:', loading, 'isInitializing:', isInitializing);

  // 显示加载界面
  if (isInitializing || loading) {
    return (
      <View
        style={[
          styles.loadingContainer,
          { backgroundColor: theme.colors.background },
        ]}
      >
        <ActivityIndicator size="large" color={theme.colors.primary} />
        <Text
          style={[
            styles.loadingText,
            { color: theme.colors.textSecondary },
          ]}
        >
          正在初始化应用...
        </Text>
      </View>
    );
  }

  // 测试登录函数
  const testLogin = async () => {
    console.log('测试登录开始');
    const result = await login('learner@example.com', '123456');
    console.log('测试登录结果:', result);
  };

  // 根据认证状态显示不同的界面
  if (isAuthenticated) {
    // 已登录：显示主应用界面
    return <SimpleAppNavigator />;
  } else {
    // 未登录：显示认证界面
    return (
      <View style={{ flex: 1 }}>
        <AuthNavigator onAuthSuccess={handleAuthSuccess} />

        {/* 测试按钮 */}
        <TouchableOpacity
          style={{
            position: 'absolute',
            top: 50,
            right: 20,
            backgroundColor: theme.colors.primary,
            padding: 10,
            borderRadius: 5,
          }}
          onPress={testLogin}
        >
          <Text style={{ color: 'white', fontSize: 12 }}>测试登录</Text>
        </TouchableOpacity>
      </View>
    );
  }
};

const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
  },
});

export default MainAppNavigator;
