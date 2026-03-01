/**
 * React Navigation 认证导航器
 * 
 * 使用React Navigation管理登录和注册页面
 */

import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import type { AuthStackParamList } from './navigation.types';

// 导入页面
import LoginScreen from '../screens/auth/LoginScreen';
import RegisterScreen from '../screens/auth/RegisterScreen';

const Stack = createNativeStackNavigator<AuthStackParamList>();

/**
 * 认证导航器
 */
export const RNAuthNavigator: React.FC = () => {
  return (
    <Stack.Navigator
      initialRouteName="Login"
      screenOptions={{
        headerShown: false, // 隐藏默认头部
        animation: 'slide_from_right', // 页面切换动画
      }}
    >
      <Stack.Screen 
        name="Login" 
        component={LoginScreen}
        options={{
          title: '登录',
        }}
      />
      
      <Stack.Screen 
        name="Register" 
        component={RegisterScreen}
        options={{
          title: '注册',
          animation: 'slide_from_bottom', // 从底部滑入
        }}
      />
    </Stack.Navigator>
  );
};

export default RNAuthNavigator;

