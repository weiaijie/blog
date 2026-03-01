/**
 * 导航类型定义
 * 
 * 为React Navigation提供完整的TypeScript类型支持
 */

import type { NavigatorScreenParams } from '@react-navigation/native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import type { BottomTabScreenProps } from '@react-navigation/bottom-tabs';

/**
 * 根导航器参数列表
 */
export type RootStackParamList = {
  Auth: NavigatorScreenParams<AuthStackParamList>;
  Main: NavigatorScreenParams<MainTabParamList>;
};

/**
 * 认证导航器参数列表
 */
export type AuthStackParamList = {
  Login: undefined;
  Register: undefined;
};

/**
 * 主应用Tab导航器参数列表
 */
export type MainTabParamList = {
  Home: undefined;
  Todo: undefined;
  Profile: undefined;
  Settings: undefined;
};

/**
 * 主应用Stack导航器参数列表（用于Modal等）
 */
export type MainStackParamList = {
  MainTabs: NavigatorScreenParams<MainTabParamList>;
  TodoDetail: {
    id: string;
    title?: string;
  };
  UserProfile: {
    userId: string;
  };
};

/**
 * 根导航器Props类型
 */
export type RootStackScreenProps<T extends keyof RootStackParamList> =
  NativeStackScreenProps<RootStackParamList, T>;

/**
 * 认证导航器Props类型
 */
export type AuthStackScreenProps<T extends keyof AuthStackParamList> =
  NativeStackScreenProps<AuthStackParamList, T>;

/**
 * Tab导航器Props类型
 */
export type MainTabScreenProps<T extends keyof MainTabParamList> =
  BottomTabScreenProps<MainTabParamList, T>;

/**
 * 主Stack导航器Props类型
 */
export type MainStackScreenProps<T extends keyof MainStackParamList> =
  NativeStackScreenProps<MainStackParamList, T>;

/**
 * 声明全局导航类型
 */
declare global {
  namespace ReactNavigation {
    interface RootParamList extends RootStackParamList {}
  }
}

