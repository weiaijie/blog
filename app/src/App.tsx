/**
 * React Native学习测试应用主组件
 *
 * 这是应用的根组件，负责：
 * 1. 设置Redux状态管理
 * 2. 设置主题管理系统
 * 3. 初始化应用导航
 */

import React from 'react';
import { Provider } from 'react-redux'; // Redux状态管理Provider
import { store } from './store'; // Redux store配置
import { ThemeProvider } from './contexts/ThemeContext'; // 主题管理Context
import AppNavigator from './navigation/AppNavigator'; // 应用导航组件

/**
 * 应用主组件
 *
 * 组件层级结构：
 * App (根组件)
 * ├── Provider (Redux状态管理)
 * │   └── ThemeProvider (主题管理)
 * │       └── AppNavigator (导航系统)
 * │           ├── HomeScreen (首页)
 * │           ├── TodoScreen (待办事项)
 * │           ├── ProfileScreen (个人中心)
 * │           └── SettingsScreen (设置页面)
 */
const App: React.FC = () => {
  return (
    // Redux Provider: 为整个应用提供状态管理
    <Provider store={store}>
      {/* 主题Provider: 为整个应用提供主题管理功能 */}
      <ThemeProvider>
        {/* 应用导航: 管理页面间的切换和路由 */}
        <AppNavigator />
      </ThemeProvider>
    </Provider>
  );
};

export default App;
