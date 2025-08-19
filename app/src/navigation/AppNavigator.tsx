/**
 * 应用主导航器
 *
 * 这是应用的核心导航系统，实现了一个自定义的Tab导航，包含：
 *
 * 主要功能：
 * 1. 底部Tab导航栏 - 提供页面间的快速切换
 * 2. 顶部标题栏 - 显示当前页面标题
 * 3. 页面渲染管理 - 根据选中的Tab渲染对应页面
 * 4. 状态管理 - 管理当前活跃的Tab状态
 * 5. 视觉反馈 - 为活跃Tab提供视觉指示
 *
 * 架构说明：
 * - 使用简单的状态管理来模拟导航
 * - 后续可以集成React Navigation来获得更强大的导航功能
 * - 采用组件化设计，易于维护和扩展
 */

import React, { useState } from 'react';
import {
  View,          // 基础容器组件
  Text,          // 文本显示组件
  TouchableOpacity, // 可点击的容器组件
  StyleSheet,    // 样式表
  SafeAreaView,  // 安全区域容器（避免刘海屏等问题）
  StatusBar,     // 状态栏组件
} from 'react-native';

// 导入所有页面组件
import HomeScreen from '../screens/home/HomeScreen';         // 首页 - 应用功能展示
import TodoScreen from '../screens/todo/TodoScreen';         // 待办 - 任务管理功能
import ProfileScreen from '../screens/profile/ProfileScreen'; // 个人 - 用户信息页面
import SettingsScreen from '../screens/settings/SettingsScreen'; // 设置 - 应用配置页面

/**
 * 页面类型定义
 * 定义了应用中所有可用的页面标识符
 */
type Screen = 'Home' | 'Todo' | 'Profile' | 'Settings';

/**
 * Tab项目的数据结构
 * 定义了每个Tab需要的基本信息
 */
interface TabItem {
  key: Screen;    // 页面标识符，用于路由和状态管理
  title: string;  // 显示在Tab上的标题文字
  icon: string;   // 显示在Tab上的图标（使用Emoji）
}

/**
 * Tab配置数组
 * 定义了应用中所有的Tab页面及其显示信息
 *
 * 每个Tab包含：
 * - key: 唯一标识符，用于路由和状态管理
 * - title: 显示名称，会出现在Tab栏和顶部标题
 * - icon: 图标，使用Emoji来保持简洁性
 */
const tabs: TabItem[] = [
  { key: 'Home', title: '首页', icon: '🏠' },      // 首页 - 应用主要功能入口
  { key: 'Todo', title: '待办', icon: '📝' },      // 待办 - 任务管理功能
  { key: 'Profile', title: '个人', icon: '👤' },   // 个人 - 用户信息和个人设置
  { key: 'Settings', title: '设置', icon: '⚙️' },  // 设置 - 应用配置和系统设置
];

/**
 * 应用导航器主组件
 *
 * 功能：
 * 1. 管理应用的整体导航结构
 * 2. 提供Tab切换功能
 * 3. 渲染当前活跃的页面
 * 4. 显示导航相关的UI元素
 */
const AppNavigator: React.FC = () => {
  // 当前活跃的Tab状态，默认为首页
  const [activeTab, setActiveTab] = useState<Screen>('Home');

  /**
   * 页面渲染函数
   *
   * 根据当前活跃的Tab渲染对应的页面组件
   * 使用switch语句来确保类型安全和性能优化
   *
   * @returns 当前活跃Tab对应的页面组件
   */
  const renderScreen = () => {
    switch (activeTab) {
      case 'Home':
        return <HomeScreen />;      // 渲染首页组件
      case 'Todo':
        return <TodoScreen />;      // 渲染待办事项页面组件
      case 'Profile':
        return <ProfileScreen />;   // 渲染个人中心页面组件
      case 'Settings':
        return <SettingsScreen />;  // 渲染设置页面组件
      default:
        return <HomeScreen />;      // 默认情况下渲染首页（容错处理）
    }
  };

  /**
   * Tab导航栏渲染函数
   *
   * 功能：
   * 1. 渲染底部的Tab导航栏
   * 2. 为每个Tab提供点击交互
   * 3. 显示活跃状态的视觉反馈
   * 4. 展示图标和标题
   *
   * @returns Tab导航栏的JSX元素
   */
  const renderTabBar = () => {
    return (
      <View style={styles.tabBar}>
        {/* 遍历所有Tab配置，为每个Tab创建一个可点击的项目 */}
        {tabs.map((tab) => (
          <TouchableOpacity
            key={tab.key}  // 使用Tab的key作为React的key
            style={[
              styles.tabItem,  // 基础Tab样式
              // 如果是当前活跃的Tab，应用活跃状态样式
              activeTab === tab.key && styles.activeTabItem,
            ]}
            onPress={() => setActiveTab(tab.key)}  // 点击时切换到对应的Tab
          >
            {/* Tab图标 */}
            <Text style={styles.tabIcon}>{tab.icon}</Text>

            {/* Tab标题 */}
            <Text
              style={[
                styles.tabTitle,  // 基础标题样式
                // 如果是当前活跃的Tab，应用活跃状态的标题样式
                activeTab === tab.key && styles.activeTabTitle,
              ]}
            >
              {tab.title}
            </Text>
          </TouchableOpacity>
        ))}
      </View>
    );
  };

  /**
   * 主渲染函数
   *
   * 渲染整个导航器的UI结构，包括：
   * 1. 安全区域容器
   * 2. 状态栏配置
   * 3. 顶部标题栏
   * 4. 主要内容区域
   * 5. 底部Tab导航栏
   */
  return (
    <SafeAreaView style={styles.container}>
      {/* 状态栏配置 - 设置为深色内容，白色背景 */}
      <StatusBar barStyle="dark-content" backgroundColor="#FFFFFF" />

      {/* 顶部导航栏 - 显示当前页面的标题 */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>
          {/* 根据当前活跃的Tab查找并显示对应的标题，如果找不到则显示默认标题 */}
          {tabs.find(tab => tab.key === activeTab)?.title || '首页'}
        </Text>
      </View>

      {/* 主要内容区域 - 渲染当前活跃Tab对应的页面组件 */}
      <View style={styles.content}>
        {renderScreen()}
      </View>

      {/* 底部Tab导航栏 - 提供页面切换功能 */}
      {renderTabBar()}
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  header: {
    height: 56,
    backgroundColor: '#FFFFFF',
    justifyContent: 'center',
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
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
    color: '#111827',
  },
  content: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  tabBar: {
    flexDirection: 'row',
    backgroundColor: '#FFFFFF',
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
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
    color: '#6B7280',
    fontWeight: '500',
  },
  activeTabTitle: {
    color: '#007AFF',
    fontWeight: '600',
  },
});

export default AppNavigator;
