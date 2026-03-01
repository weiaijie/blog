/**
 * React Navigation 根导航器
 * 
 * 应用的主导航器，根据认证状态显示不同的导航流程
 */

import React, { useEffect } from 'react';
import { Platform } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import type { RootStackParamList } from './navigation.types';
import { linking } from './linking';
import { useAuthContext } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';

// 导入导航器
import RNAuthNavigator from './RNAuthNavigator';
import RNMainNavigator from './RNMainNavigator';

const Stack = createNativeStackNavigator<RootStackParamList>();

/**
 * 根导航器组件
 */
export const RNAppNavigator: React.FC = () => {
  const { isAuthenticated, checkAuth } = useAuthContext();
  const { theme } = useTheme();

  // 应用启动时检查认证状态
  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  // 导航主题配置
  const navigationTheme = {
    dark: theme.mode === 'dark',
    colors: {
      primary: theme.colors.primary,
      background: theme.colors.background,
      card: theme.colors.surface,
      text: theme.colors.text,
      border: theme.colors.border,
      notification: theme.colors.error,
    },
  };

  return (
    <NavigationContainer
      linking={linking}
      theme={navigationTheme}
      documentTitle={{
        formatter: (options, route) => {
          // 自定义页面标题
          const routeName = route?.name || 'Home';
          return `${routeName} - React Native 学习应用`;
        },
      }}
      onReady={() => {
        console.log('导航系统已就绪');
        
        // Web端：更新页面标题
        if (Platform.OS === 'web') {
          document.title = 'React Native 学习应用';
        }
      }}
      onStateChange={(state) => {
        // 可选：监听导航状态变化
        console.log('导航状态变化:', state);
      }}
    >
      <Stack.Navigator
        screenOptions={{
          headerShown: false, // 隐藏Stack的默认头部
          animation: 'fade', // 认证状态切换时使用淡入淡出动画
        }}
      >
        {!isAuthenticated ? (
          // 未登录：显示认证流程
          <Stack.Screen 
            name="Auth" 
            component={RNAuthNavigator}
            options={{
              animationTypeForReplace: 'pop', // 登出时使用pop动画
            }}
          />
        ) : (
          // 已登录：显示主应用
          <Stack.Screen 
            name="Main" 
            component={RNMainNavigator}
            options={{
              animationTypeForReplace: 'push', // 登录时使用push动画
            }}
          />
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
};

export default RNAppNavigator;

