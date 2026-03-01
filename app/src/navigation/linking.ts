/**
 * Linking配置
 * 
 * 配置深度链接和Web URL路由
 * 支持移动端深度链接和Web端URL路由
 */

import { LinkingOptions } from '@react-navigation/native';
import { Platform } from 'react-native';
import type { RootStackParamList } from './navigation.types';

/**
 * Linking配置
 */
export const linking: LinkingOptions<RootStackParamList> = {
  // URL前缀配置
  prefixes: [
    // Web端URL前缀
    ...(Platform.OS === 'web' 
      ? [
          'http://localhost:3000',
          'http://localhost:19006', // Expo web
          'https://yourapp.com',     // 生产环境域名
        ]
      : []
    ),
    // 移动端深度链接前缀
    'rnlearningapp://',
    'myapp://',
  ],

  // 路由配置
  config: {
    screens: {
      // 认证流程
      Auth: {
        screens: {
          Login: 'login',
          Register: 'register',
        },
      },
      
      // 主应用
      Main: {
        screens: {
          Home: '',              // 根路径 /
          Todo: 'todo',          // /todo
          Profile: 'profile',    // /profile
          Settings: 'settings',  // /settings
        },
      },
    },
  },

  // 可选：自定义URL解析
  async getInitialURL() {
    if (Platform.OS === 'web') {
      return window.location.href;
    }
    
    // 移动端：检查深度链接
    // const url = await Linking.getInitialURL();
    // return url;
    return null;
  },

  // 可选：订阅URL变化
  subscribe(listener) {
    if (Platform.OS === 'web') {
      // Web端：监听浏览器URL变化
      const onPopState = () => {
        listener(window.location.href);
      };

      window.addEventListener('popstate', onPopState);

      return () => {
        window.removeEventListener('popstate', onPopState);
      };
    }

    // 移动端：监听深度链接
    // const subscription = Linking.addEventListener('url', ({ url }) => {
    //   listener(url);
    // });
    // return () => subscription.remove();
    
    return () => {};
  },
};

/**
 * 导航到指定URL（用于外部调用）
 */
export const navigateToURL = (url: string) => {
  if (Platform.OS === 'web') {
    window.history.pushState({}, '', url);
  }
};

/**
 * 获取当前URL路径
 */
export const getCurrentPath = (): string => {
  if (Platform.OS === 'web') {
    return window.location.pathname;
  }
  return '/';
};

export default linking;

