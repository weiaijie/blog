/**
 * Web应用导航器（带URL路由）
 * 
 * 使用浏览器History API实现URL路由
 * 支持浏览器前进/后退按钮
 * 支持直接访问特定URL
 */

import React, { useState, useEffect } from 'react';
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
 * 路由配置
 */
interface RouteConfig {
  key: Screen;
  path: string;
  title: string;
  icon: string;
  component: React.ComponentType;
}

const routes: RouteConfig[] = [
  { key: 'Home', path: '/', title: '首页', icon: '🏠', component: HomeScreen },
  { key: 'Todo', path: '/todo', title: '待办', icon: '📝', component: TodoScreen },
  { key: 'Profile', path: '/profile', title: '个人', icon: '👤', component: ProfileScreen },
  { key: 'Settings', path: '/settings', title: '设置', icon: '⚙️', component: SettingsScreen },
];

/**
 * Web应用导航器（带URL路由）
 */
export const WebAppNavigator: React.FC = () => {
  const { theme } = useTheme();
  const [activeTab, setActiveTab] = useState<Screen>('Home');

  // 根据URL路径获取对应的路由
  const getRouteFromPath = (pathname: string): Screen => {
    const route = routes.find(r => r.path === pathname);
    return route ? route.key : 'Home';
  };

  // 初始化：根据当前URL设置活动Tab
  useEffect(() => {
    if (Platform.OS === 'web') {
      const currentPath = window.location.pathname;
      const screen = getRouteFromPath(currentPath);
      setActiveTab(screen);
    }
  }, []);

  // 监听浏览器前进/后退按钮
  useEffect(() => {
    if (Platform.OS === 'web') {
      const handlePopState = () => {
        const currentPath = window.location.pathname;
        const screen = getRouteFromPath(currentPath);
        setActiveTab(screen);
      };

      window.addEventListener('popstate', handlePopState);
      return () => window.removeEventListener('popstate', handlePopState);
    }
  }, []);

  /**
   * 导航到指定页面
   */
  const navigateTo = (screen: Screen) => {
    const route = routes.find(r => r.key === screen);
    if (!route) return;

    setActiveTab(screen);

    // 更新浏览器URL
    if (Platform.OS === 'web') {
      window.history.pushState(
        { screen },
        route.title,
        route.path
      );
      // 更新页面标题
      document.title = `${route.title} - React Native 学习应用`;
    }
  };

  /**
   * 页面渲染函数
   */
  const renderScreen = () => {
    const route = routes.find(r => r.key === activeTab);
    if (!route) return <HomeScreen />;
    
    const Component = route.component;
    return <Component />;
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
        {routes.map((route) => (
          <TouchableOpacity
            key={route.key}
            style={[
              styles.tabItem,
              activeTab === route.key && styles.activeTabItem,
            ]}
            onPress={() => navigateTo(route.key)}
          >
            <Text style={styles.tabIcon}>{route.icon}</Text>
            <Text
              style={[
                styles.tabTitle,
                { color: theme.colors.textSecondary },
                activeTab === route.key && {
                  color: theme.colors.primary,
                  fontWeight: '600',
                },
              ]}
            >
              {route.title}
            </Text>
            
            {/* 活动指示器 */}
            {activeTab === route.key && (
              <View
                style={[
                  styles.activeIndicator,
                  { backgroundColor: theme.colors.primary },
                ]}
              />
            )}
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
          {routes.find(r => r.key === activeTab)?.title || '首页'}
        </Text>
        
        {/* 显示当前路径（调试用） */}
        {Platform.OS === 'web' && (
          <Text
            style={[
              styles.pathText,
              { color: theme.colors.textSecondary },
            ]}
          >
            {routes.find(r => r.key === activeTab)?.path}
          </Text>
        )}
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
  pathText: {
    fontSize: 12,
    marginTop: 2,
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
    position: 'relative',
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
  activeIndicator: {
    position: 'absolute',
    top: 0,
    left: '25%',
    right: '25%',
    height: 3,
    borderRadius: 1.5,
  },
});

export default WebAppNavigator;
