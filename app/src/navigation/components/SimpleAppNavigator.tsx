/**
 * 简化版应用导航器
 * 
 * 这是一个简化的导航器，避免复杂的依赖问题，提供基本的导航功能
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  SafeAreaView,
  StatusBar,
  TouchableOpacity,
  Platform,
} from 'react-native';
import { useTheme } from '../../contexts/ThemeContext';
import WebAppNavigator from './WebAppNavigator';

// 导入页面组件
import HomeScreen from '../../screens/home/HomeScreen';
import TodoScreen from '../../screens/todo/TodoScreen';
import ProfileScreen from '../../screens/profile/ProfileScreen';
import SettingsScreen from '../../screens/settings/SettingsScreen';

/**
 * 页面类型定义
 */
type Screen = 'Home' | 'Todo' | 'Profile' | 'Settings';

/**
 * Tab项目的数据结构
 */
interface TabItem {
  key: Screen;
  title: string;
  icon: string;
}

/**
 * Tab配置数组
 */
const tabs: TabItem[] = [
  { key: 'Home', title: '首页', icon: '🏠' },
  { key: 'Todo', title: '待办', icon: '📝' },
  { key: 'Profile', title: '个人', icon: '👤' },
  { key: 'Settings', title: '设置', icon: '⚙️' },
];

/**
 * 简化版应用导航器
 */
export const SimpleAppNavigator: React.FC = () => {
  // 在Web平台使用带URL路由的导航器
  if (Platform.OS === 'web') {
    return <WebAppNavigator />;
  }

  // 在移动平台使用简单的状态导航
  const { theme } = useTheme();
  const [activeTab, setActiveTab] = useState<Screen>('Home');

  /**
   * 页面渲染函数
   */
  const renderScreen = () => {
    switch (activeTab) {
      case 'Home':
        return <HomeScreen />;
      case 'Todo':
        return <TodoScreen />;
      case 'Profile':
        return <ProfileScreen />;
      case 'Settings':
        return <SettingsScreen />;
      default:
        return <HomeScreen />;
    }
  };

  /**
   * Tab导航栏渲染函数
   */
  const renderTabBar = () => {
    return (
      <View
        style={[
          styles.tabBar,
          {
            backgroundColor: theme.colors.surface,
            borderTopColor: theme.colors.border,
          },
        ]}
      >
        {tabs.map((tab) => (
          <TouchableOpacity
            key={tab.key}
            style={[
              styles.tabItem,
              activeTab === tab.key && styles.activeTabItem,
            ]}
            onPress={() => setActiveTab(tab.key)}
          >
            <Text style={styles.tabIcon}>{tab.icon}</Text>
            <Text
              style={[
                styles.tabTitle,
                { color: theme.colors.textSecondary },
                activeTab === tab.key && {
                  color: theme.colors.primary,
                  fontWeight: '600',
                },
              ]}
            >
              {tab.title}
            </Text>
          </TouchableOpacity>
        ))}
      </View>
    );
  };

  return (
    <SafeAreaView
      style={[
        styles.container,
        { backgroundColor: theme.colors.surface },
      ]}
    >
      {/* 状态栏配置 */}
      <StatusBar
        barStyle={theme.mode === 'dark' ? 'light-content' : 'dark-content'}
        backgroundColor={theme.colors.surface}
      />

      {/* 顶部导航栏 */}
      <View
        style={[
          styles.header,
          {
            backgroundColor: theme.colors.surface,
            borderBottomColor: theme.colors.border,
          },
        ]}
      >
        <Text
          style={[
            styles.headerTitle,
            { color: theme.colors.text },
          ]}
        >
          {tabs.find(tab => tab.key === activeTab)?.title || '首页'}
        </Text>
      </View>

      {/* 主要内容区域 */}
      <View
        style={[
          styles.content,
          { backgroundColor: theme.colors.background },
        ]}
      >
        {renderScreen()}
      </View>

      {/* 底部Tab导航栏 */}
      {renderTabBar()}
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    height: 56,
    justifyContent: 'center',
    alignItems: 'center',
    borderBottomWidth: 1,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 1,
    },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
  },
  content: {
    flex: 1,
  },
  tabBar: {
    flexDirection: 'row',
    borderTopWidth: 1,
    paddingBottom: 8,
    paddingTop: 8,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: -1,
    },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 8,
  },
  tabItem: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: 8,
    paddingHorizontal: 4,
  },
  activeTabItem: {
    // 可以添加激活状态的样式
  },
  tabIcon: {
    fontSize: 20,
    marginBottom: 4,
  },
  tabTitle: {
    fontSize: 12,
    fontWeight: '500',
  },
});

export default SimpleAppNavigator;
