// 导航相关类型定义
import { NavigatorScreenParams } from '@react-navigation/native';
import { StackScreenProps } from '@react-navigation/stack';
import { BottomTabScreenProps } from '@react-navigation/bottom-tabs';

// 根导航参数类型
export type RootStackParamList = {
  Auth: NavigatorScreenParams<AuthStackParamList>;
  Main: NavigatorScreenParams<MainTabParamList>;
  Modal: { title: string; content: string };
};

// 认证导航参数类型
export type AuthStackParamList = {
  Login: undefined;
  Register: undefined;
  ForgotPassword: undefined;
  ResetPassword: { token: string };
};

// 主要Tab导航参数类型
export type MainTabParamList = {
  Home: NavigatorScreenParams<HomeStackParamList>;
  Profile: NavigatorScreenParams<ProfileStackParamList>;
  Settings: undefined;
};

// 首页导航参数类型
export type HomeStackParamList = {
  Dashboard: undefined;
  Details: { id: string };
  Search: { query?: string };
};

// 个人中心导航参数类型
export type ProfileStackParamList = {
  Profile: undefined;
  EditProfile: undefined;
  ChangePassword: undefined;
};

// 导航Props类型定义
export type RootStackScreenProps<T extends keyof RootStackParamList> = 
  StackScreenProps<RootStackParamList, T>;

export type AuthStackScreenProps<T extends keyof AuthStackParamList> = 
  StackScreenProps<AuthStackParamList, T>;

export type MainTabScreenProps<T extends keyof MainTabParamList> = 
  BottomTabScreenProps<MainTabParamList, T>;

export type HomeStackScreenProps<T extends keyof HomeStackParamList> = 
  StackScreenProps<HomeStackParamList, T>;

export type ProfileStackScreenProps<T extends keyof ProfileStackParamList> = 
  StackScreenProps<ProfileStackParamList, T>;

// 导航状态类型
export interface NavigationState {
  isLoading: boolean;
  currentRoute?: string;
  previousRoute?: string;
}

// 深度链接类型
export interface DeepLinkConfig {
  screens: {
    [key: string]: string | DeepLinkConfig;
  };
}

declare global {
  namespace ReactNavigation {
    interface RootParamList extends RootStackParamList {}
  }
}
