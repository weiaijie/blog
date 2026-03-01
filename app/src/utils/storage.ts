// 本地存储工具
import AsyncStorage from '@react-native-async-storage/async-storage';
import { STORAGE_KEYS } from './constants';

// 存储工具类
export class StorageUtil {
  // 存储字符串
  static async setString(key: string, value: string): Promise<void> {
    try {
      await AsyncStorage.setItem(key, value);
    } catch (error) {
      console.error('Error storing string:', error);
      throw error;
    }
  }

  // 获取字符串
  static async getString(key: string): Promise<string | null> {
    try {
      return await AsyncStorage.getItem(key);
    } catch (error) {
      console.error('Error getting string:', error);
      return null;
    }
  }

  // 存储对象
  static async setObject(key: string, value: any): Promise<void> {
    try {
      const jsonValue = JSON.stringify(value);
      await AsyncStorage.setItem(key, jsonValue);
    } catch (error) {
      console.error('Error storing object:', error);
      throw error;
    }
  }

  // 获取对象
  static async getObject<T>(key: string): Promise<T | null> {
    try {
      const jsonValue = await AsyncStorage.getItem(key);
      return jsonValue != null ? JSON.parse(jsonValue) : null;
    } catch (error) {
      console.error('Error getting object:', error);
      return null;
    }
  }

  // 存储布尔值
  static async setBoolean(key: string, value: boolean): Promise<void> {
    try {
      await AsyncStorage.setItem(key, JSON.stringify(value));
    } catch (error) {
      console.error('Error storing boolean:', error);
      throw error;
    }
  }

  // 获取布尔值
  static async getBoolean(key: string): Promise<boolean | null> {
    try {
      const value = await AsyncStorage.getItem(key);
      return value != null ? JSON.parse(value) : null;
    } catch (error) {
      console.error('Error getting boolean:', error);
      return null;
    }
  }

  // 存储数字
  static async setNumber(key: string, value: number): Promise<void> {
    try {
      await AsyncStorage.setItem(key, JSON.stringify(value));
    } catch (error) {
      console.error('Error storing number:', error);
      throw error;
    }
  }

  // 获取数字
  static async getNumber(key: string): Promise<number | null> {
    try {
      const value = await AsyncStorage.getItem(key);
      return value != null ? JSON.parse(value) : null;
    } catch (error) {
      console.error('Error getting number:', error);
      return null;
    }
  }

  // 删除指定键
  static async remove(key: string): Promise<void> {
    try {
      await AsyncStorage.removeItem(key);
    } catch (error) {
      console.error('Error removing item:', error);
      throw error;
    }
  }

  // 清空所有存储
  static async clear(): Promise<void> {
    try {
      await AsyncStorage.clear();
    } catch (error) {
      console.error('Error clearing storage:', error);
      throw error;
    }
  }

  // 获取所有键
  static async getAllKeys(): Promise<string[]> {
    try {
      return await AsyncStorage.getAllKeys();
    } catch (error) {
      console.error('Error getting all keys:', error);
      return [];
    }
  }

  // 检查键是否存在
  static async hasKey(key: string): Promise<boolean> {
    try {
      const keys = await AsyncStorage.getAllKeys();
      return keys.includes(key);
    } catch (error) {
      console.error('Error checking key existence:', error);
      return false;
    }
  }
}

// 认证相关存储
export const AuthStorage = {
  // 存储认证token
  setAuthToken: (token: string) => 
    StorageUtil.setString(STORAGE_KEYS.AUTH_TOKEN, token),
  
  // 获取认证token
  getAuthToken: () => 
    StorageUtil.getString(STORAGE_KEYS.AUTH_TOKEN),
  
  // 存储刷新token
  setRefreshToken: (token: string) => 
    StorageUtil.setString(STORAGE_KEYS.REFRESH_TOKEN, token),
  
  // 获取刷新token
  getRefreshToken: () => 
    StorageUtil.getString(STORAGE_KEYS.REFRESH_TOKEN),
  
  // 存储用户信息
  setUserInfo: (userInfo: any) => 
    StorageUtil.setObject(STORAGE_KEYS.USER_INFO, userInfo),
  
  // 获取用户信息
  getUserInfo: () => 
    StorageUtil.getObject(STORAGE_KEYS.USER_INFO),
  
  // 清除认证信息
  clearAuthData: async () => {
    await Promise.all([
      StorageUtil.remove(STORAGE_KEYS.AUTH_TOKEN),
      StorageUtil.remove(STORAGE_KEYS.REFRESH_TOKEN),
      StorageUtil.remove(STORAGE_KEYS.USER_INFO),
    ]);
  },
};

// 应用设置存储
export const SettingsStorage = {
  // 存储主题设置
  setTheme: (theme: string) => 
    StorageUtil.setString(STORAGE_KEYS.THEME, theme),
  
  // 获取主题设置
  getTheme: () => 
    StorageUtil.getString(STORAGE_KEYS.THEME),
  
  // 存储语言设置
  setLanguage: (language: string) => 
    StorageUtil.setString(STORAGE_KEYS.LANGUAGE, language),
  
  // 获取语言设置
  getLanguage: () => 
    StorageUtil.getString(STORAGE_KEYS.LANGUAGE),
  
  // 存储生物识别设置
  setBiometricEnabled: (enabled: boolean) => 
    StorageUtil.setBoolean(STORAGE_KEYS.BIOMETRIC_ENABLED, enabled),
  
  // 获取生物识别设置
  getBiometricEnabled: () => 
    StorageUtil.getBoolean(STORAGE_KEYS.BIOMETRIC_ENABLED),
  
  // 存储首次启动标记
  setFirstLaunch: (isFirst: boolean) => 
    StorageUtil.setBoolean(STORAGE_KEYS.FIRST_LAUNCH, isFirst),
  
  // 获取首次启动标记
  getFirstLaunch: () => 
    StorageUtil.getBoolean(STORAGE_KEYS.FIRST_LAUNCH),
};

export default StorageUtil;
