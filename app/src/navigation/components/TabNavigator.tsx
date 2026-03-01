/**
 * 增强版Tab导航组件
 * 
 * 这是一个功能丰富的Tab导航组件，提供：
 * 1. 动态Tab配置
 * 2. 徽章支持
 * 3. 切换动画
 * 4. 自定义样式
 * 5. 主题支持
 * 6. 手势支持
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Animated,
  Dimensions,
  Platform,
} from 'react-native';
import { useTheme } from '../../contexts/ThemeContext';
import { useNavigation, useRoute, useNavigationState } from '../NavigationContext';
import { RouteConfig, RouteName } from '../types';
import { getTabRoutes } from '../config/routes';

/**
 * Tab项徽章配置
 */
interface TabBadge {
  count?: number;           // 徽章数字
  dot?: boolean;           // 是否显示小红点
  color?: string;          // 徽章颜色
  textColor?: string;      // 徽章文字颜色
}

/**
 * Tab导航器属性
 */
interface TabNavigatorProps {
  routes?: RouteConfig[];                    // 自定义路由配置
  badges?: Record<RouteName, TabBadge>;      // 徽章配置
  tabBarStyle?: any;                         // 自定义Tab栏样式
  tabItemStyle?: any;                        // 自定义Tab项样式
  activeTabColor?: string;                   // 活跃Tab颜色
  inactiveTabColor?: string;                 // 非活跃Tab颜色
  showLabels?: boolean;                      // 是否显示标签
  animationEnabled?: boolean;                // 是否启用动画
  onTabPress?: (route: RouteName) => void;   // Tab点击回调
}

/**
 * Tab项组件
 */
interface TabItemProps {
  route: RouteConfig;
  isActive: boolean;
  badge?: TabBadge;
  activeColor: string;
  inactiveColor: string;
  showLabel: boolean;
  animationEnabled: boolean;
  onPress: () => void;
}

const TabItem: React.FC<TabItemProps> = ({
  route,
  isActive,
  badge,
  activeColor,
  inactiveColor,
  showLabel,
  animationEnabled,
  onPress,
}) => {
  const [scaleAnim] = useState(new Animated.Value(1));
  const [opacityAnim] = useState(new Animated.Value(isActive ? 1 : 0.6));

  // 动画效果
  useEffect(() => {
    if (animationEnabled) {
      Animated.parallel([
        Animated.spring(scaleAnim, {
          toValue: isActive ? 1.1 : 1,
          useNativeDriver: true,
          tension: 300,
          friction: 10,
        }),
        Animated.timing(opacityAnim, {
          toValue: isActive ? 1 : 0.6,
          duration: 200,
          useNativeDriver: true,
        }),
      ]).start();
    }
  }, [isActive, animationEnabled]);

  const handlePress = () => {
    if (animationEnabled) {
      // 点击动画
      Animated.sequence([
        Animated.timing(scaleAnim, {
          toValue: 0.95,
          duration: 100,
          useNativeDriver: true,
        }),
        Animated.timing(scaleAnim, {
          toValue: isActive ? 1.1 : 1,
          duration: 100,
          useNativeDriver: true,
        }),
      ]).start();
    }
    onPress();
  };

  const iconColor = isActive ? activeColor : inactiveColor;
  const textColor = isActive ? activeColor : inactiveColor;

  return (
    <TouchableOpacity
      style={styles.tabItem}
      onPress={handlePress}
      activeOpacity={0.7}
    >
      <Animated.View
        style={[
          styles.tabContent,
          {
            transform: [{ scale: scaleAnim }],
            opacity: opacityAnim,
          },
        ]}
      >
        {/* 图标容器 */}
        <View style={styles.iconContainer}>
          <Text style={[styles.tabIcon, { color: iconColor }]}>
            {route.icon}
          </Text>
          
          {/* 徽章 */}
          {badge && (
            <View style={styles.badgeContainer}>
              {badge.dot ? (
                <View
                  style={[
                    styles.badgeDot,
                    { backgroundColor: badge.color || '#FF3B30' },
                  ]}
                />
              ) : badge.count && badge.count > 0 ? (
                <View
                  style={[
                    styles.badgeCount,
                    { backgroundColor: badge.color || '#FF3B30' },
                  ]}
                >
                  <Text
                    style={[
                      styles.badgeText,
                      { color: badge.textColor || '#FFFFFF' },
                    ]}
                  >
                    {badge.count > 99 ? '99+' : badge.count.toString()}
                  </Text>
                </View>
              ) : null}
            </View>
          )}
        </View>

        {/* 标签 */}
        {showLabel && (
          <Text
            style={[
              styles.tabLabel,
              { color: textColor },
              isActive && styles.activeTabLabel,
            ]}
          >
            {route.title}
          </Text>
        )}

        {/* 活跃指示器 */}
        {isActive && (
          <View
            style={[
              styles.activeIndicator,
              { backgroundColor: activeColor },
            ]}
          />
        )}
      </Animated.View>
    </TouchableOpacity>
  );
};

/**
 * Tab导航器主组件
 */
export const TabNavigator: React.FC<TabNavigatorProps> = ({
  routes = getTabRoutes(),
  badges = {},
  tabBarStyle,
  tabItemStyle,
  activeTabColor,
  inactiveTabColor,
  showLabels = true,
  animationEnabled = true,
  onTabPress,
}) => {
  const { theme } = useTheme();
  const navigation = useNavigation();
  const currentRoute = useRoute();
  const { isCurrentRoute } = useNavigationState();

  // 主题颜色
  const activeColor = activeTabColor || theme.colors.primary;
  const inactiveColor = inactiveTabColor || theme.colors.textSecondary;

  // 处理Tab点击
  const handleTabPress = async (route: RouteConfig) => {
    try {
      // 执行自定义回调
      if (onTabPress) {
        onTabPress(route.name);
      }

      // 导航到目标路由
      if (!isCurrentRoute(route.name)) {
        await navigation.navigate(route.name);
      }
    } catch (error) {
      console.error('Tab navigation error:', error);
    }
  };

  return (
    <View
      style={[
        styles.tabBar,
        {
          backgroundColor: theme.colors.surface,
          borderTopColor: theme.colors.border,
        },
        tabBarStyle,
      ]}
    >
      {routes.map((route) => (
        <TabItem
          key={route.name}
          route={route}
          isActive={isCurrentRoute(route.name)}
          badge={badges[route.name]}
          activeColor={activeColor}
          inactiveColor={inactiveColor}
          showLabel={showLabels}
          animationEnabled={animationEnabled}
          onPress={() => handleTabPress(route)}
        />
      ))}
    </View>
  );
};

const styles = StyleSheet.create({
  tabBar: {
    flexDirection: 'row',
    borderTopWidth: 1,
    paddingBottom: Platform.OS === 'ios' ? 20 : 8,
    paddingTop: 8,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: -2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 8,
  },
  tabItem: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 8,
    paddingHorizontal: 4,
  },
  tabContent: {
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative',
  },
  iconContainer: {
    position: 'relative',
    alignItems: 'center',
    justifyContent: 'center',
  },
  tabIcon: {
    fontSize: 22,
    marginBottom: 4,
  },
  tabLabel: {
    fontSize: 11,
    fontWeight: '500',
    textAlign: 'center',
  },
  activeTabLabel: {
    fontWeight: '600',
  },
  activeIndicator: {
    position: 'absolute',
    bottom: -12,
    width: 4,
    height: 4,
    borderRadius: 2,
  },
  badgeContainer: {
    position: 'absolute',
    top: -8,
    right: -8,
  },
  badgeDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  badgeCount: {
    minWidth: 16,
    height: 16,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 4,
  },
  badgeText: {
    fontSize: 10,
    fontWeight: '600',
    textAlign: 'center',
  },
});

export default TabNavigator;
