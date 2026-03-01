/**
 * 认证导航器
 * 
 * 管理登录和注册页面的导航，提供：
 * 1. 登录页面
 * 2. 注册页面
 * 3. 页面间的切换
 * 4. 认证成功后的回调处理
 */

import React, { useState } from 'react';
import {
  View,
  StyleSheet,
  SafeAreaView,
  StatusBar,
} from 'react-native';
import { useTheme } from '../../contexts/ThemeContext';
import LoginScreen from '../../screens/auth/LoginScreen';
import RegisterScreen from '../../screens/auth/RegisterScreen';

/**
 * 认证页面类型
 */
type AuthScreen = 'Login' | 'Register';

/**
 * 认证导航器属性
 */
interface AuthNavigatorProps {
  onAuthSuccess?: () => void;  // 认证成功回调
  initialScreen?: AuthScreen; // 初始显示的页面
}

/**
 * 认证导航器组件
 */
export const AuthNavigator: React.FC<AuthNavigatorProps> = ({
  onAuthSuccess,
  initialScreen = 'Login',
}) => {
  const { theme } = useTheme();
  const [currentScreen, setCurrentScreen] = useState<AuthScreen>(initialScreen);

  // 处理登录成功
  const handleLoginSuccess = () => {
    if (onAuthSuccess) {
      onAuthSuccess();
    }
  };

  // 处理注册成功
  const handleRegisterSuccess = () => {
    if (onAuthSuccess) {
      onAuthSuccess();
    }
  };

  // 切换到注册页面
  const switchToRegister = () => {
    setCurrentScreen('Register');
  };

  // 切换到登录页面
  const switchToLogin = () => {
    setCurrentScreen('Login');
  };

  // 渲染当前页面
  const renderCurrentScreen = () => {
    switch (currentScreen) {
      case 'Login':
        return (
          <LoginScreen
            onLoginSuccess={handleLoginSuccess}
            onSwitchToRegister={switchToRegister}
          />
        );
      case 'Register':
        return (
          <RegisterScreen
            onRegisterSuccess={handleRegisterSuccess}
            onSwitchToLogin={switchToLogin}
          />
        );
      default:
        return (
          <LoginScreen
            onLoginSuccess={handleLoginSuccess}
            onSwitchToRegister={switchToRegister}
          />
        );
    }
  };

  return (
    <SafeAreaView
      style={[
        styles.container,
        { backgroundColor: theme.colors.background },
      ]}
    >
      {/* 状态栏配置 */}
      <StatusBar
        barStyle={theme.mode === 'dark' ? 'light-content' : 'dark-content'}
        backgroundColor={theme.colors.background}
      />

      {/* 认证页面内容 */}
      <View style={styles.content}>
        {renderCurrentScreen()}
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  content: {
    flex: 1,
  },
});

export default AuthNavigator;
