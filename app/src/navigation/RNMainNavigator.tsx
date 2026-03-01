/**
 * React Navigation 主应用导航器
 * 
 * 使用React Navigation的Tab导航管理主应用页面
 */

import React from 'react';
import { Platform, Text } from 'react-native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import type { MainTabParamList } from './navigation.types';
import { useTheme } from '../contexts/ThemeContext';

// 导入页面
import HomeScreen from '../screens/home/HomeScreen';
import TodoScreen from '../screens/todo/TodoScreen';
import ProfileScreen from '../screens/profile/ProfileScreen';
import SettingsScreen from '../screens/settings/SettingsScreen';
import CheckinScreen from '../screens/activity/CheckinScreen';

const Tab = createBottomTabNavigator<MainTabParamList>();

/**
 * Tab图标组件
 */
const TabIcon: React.FC<{ icon: string; focused: boolean; color: string }> = ({
  icon,
  focused,
}) => {
  return (
    <Text style={{ fontSize: focused ? 24 : 20 }}>
      {icon}
    </Text>
  );
};

/**
 * 主应用Tab导航器
 */
export const RNMainNavigator: React.FC = () => {
  const { theme } = useTheme();

  return (
    <Tab.Navigator
      initialRouteName="Home"
      screenOptions={{
        // 头部配置
        headerShown: true,
        headerStyle: {
          backgroundColor: theme.colors.surface,
        },
        headerTintColor: theme.colors.text,
        headerTitleStyle: {
          fontWeight: '600',
        },
        
        // Tab栏配置
        tabBarActiveTintColor: theme.colors.primary,
        tabBarInactiveTintColor: theme.colors.textSecondary,
        tabBarStyle: {
          backgroundColor: theme.colors.surface,
          borderTopColor: theme.colors.border,
          borderTopWidth: 1,
          paddingBottom: Platform.OS === 'ios' ? 20 : 8,
          paddingTop: 8,
          height: Platform.OS === 'ios' ? 88 : 64,
        },
        tabBarLabelStyle: {
          fontSize: 12,
          fontWeight: '500',
        },
      }}
    >
      <Tab.Screen
        name="Home"
        component={HomeScreen}
        options={{
          title: '首页',
          tabBarLabel: '首页',
          tabBarIcon: ({ focused, color }) => (
            <TabIcon icon="🏠" focused={focused} color={color} />
          ),
        }}
      />

      <Tab.Screen
        name="Checkin"
        component={CheckinScreen}
        options={{
          title: '签到积分',
          tabBarLabel: '签到',
          tabBarIcon: ({ focused, color }) => (
            <TabIcon icon="⭐" focused={focused} color={color} />
          ),
        }}
      />

      <Tab.Screen
        name="Profile"
        component={ProfileScreen}
        options={{
          title: '个人',
          tabBarLabel: '个人',
          tabBarIcon: ({ focused, color }) => (
            <TabIcon icon="👤" focused={focused} color={color} />
          ),
        }}
      />

      <Tab.Screen
        name="Settings"
        component={SettingsScreen}
        options={{
          title: '设置',
          tabBarLabel: '设置',
          tabBarIcon: ({ focused, color }) => (
            <TabIcon icon="⚙️" focused={focused} color={color} />
          ),
        }}
      />
    </Tab.Navigator>
  );
};

export default RNMainNavigator;

