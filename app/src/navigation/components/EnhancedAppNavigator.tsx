/**
 * 增强版应用导航器
 * 
 * 这是集成了新导航系统的主导航器，提供：
 * 1. 新的导航系统集成
 * 2. 动态路由渲染
 * 3. 导航状态管理
 * 4. 主题支持
 * 5. 错误边界
 */

import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  SafeAreaView,
  StatusBar,
  ActivityIndicator,
} from 'react-native';
import { useTheme } from '../../contexts/ThemeContext';
import { 
  NavigationProvider, 
  useRoute, 
  useNavigationState,
  useNavigation 
} from '../NavigationContext';
import { TabNavigator } from './TabNavigator';
import { router } from '../Router';
import { allRoutes } from '../config/routes';
import { RouteName } from '../types';

/**
 * 导航头部组件
 */
interface NavigationHeaderProps {
  title: string;
  canGoBack: boolean;
  onBackPress?: () => void;
}

const NavigationHeader: React.FC<NavigationHeaderProps> = ({
  title,
  canGoBack,
  onBackPress,
}) => {
  const { theme } = useTheme();

  const handleBackPress = () => {
    if (onBackPress) {
      onBackPress();
    } else {
      router.goBack().catch(console.error);
    }
  };

  return (
    <View
      style={[
        styles.header,
        {
          backgroundColor: theme.colors.surface,
          borderBottomColor: theme.colors.border,
        },
      ]}
    >
      {canGoBack && (
        <Text
          style={[styles.backButton, { color: theme.colors.primary }]}
          onPress={handleBackPress}
        >
          ← 返回
        </Text>
      )}
      <Text
        style={[
          styles.headerTitle,
          { color: theme.colors.text },
          canGoBack && styles.headerTitleWithBack,
        ]}
      >
        {title}
      </Text>
    </View>
  );
};

/**
 * 页面渲染器组件
 */
interface PageRendererProps {
  currentRoute: string;
}

const PageRenderer: React.FC<PageRendererProps> = ({ currentRoute }) => {
  const { theme } = useTheme();

  // 查找当前路由配置
  const routeConfig = allRoutes.find(r => r.name === currentRoute);

  if (!routeConfig) {
    return (
      <View style={[styles.errorContainer, { backgroundColor: theme.colors.background }]}>
        <Text style={[styles.errorText, { color: theme.colors.error }]}>
          页面未找到: {currentRoute}
        </Text>
      </View>
    );
  }

  // 渲染页面组件
  const PageComponent = routeConfig.component;

  return (
    <View style={[styles.pageContainer, { backgroundColor: theme.colors.background }]}>
      <PageComponent />
    </View>
  );
};

/**
 * 主导航器内容组件
 */
const NavigatorContent: React.FC = () => {
  const { theme } = useTheme();
  const [isLoading, setIsLoading] = useState(false);
  const [currentRoute, setCurrentRoute] = useState<string>('Home');
  const [canGoBack, setCanGoBack] = useState(false);

  // 查找当前路由配置
  const routeConfig = allRoutes.find(r => r.name === currentRoute);
  const showHeader = routeConfig?.headerShown !== false;
  const showTabBar = routeConfig?.tabBarVisible !== false;

  // 监听导航状态变化
  useEffect(() => {
    const handleNavigationStart = () => setIsLoading(true);
    const handleNavigationEnd = () => {
      setIsLoading(false);
      setCurrentRoute(router.getState().currentRoute);
      setCanGoBack(router.getState().canGoBack);
    };

    router.addEventListener('beforeNavigate', handleNavigationStart);
    router.addEventListener('afterNavigate', handleNavigationEnd);
    router.addEventListener('navigationError', handleNavigationEnd);
    router.addEventListener('routeChange', handleNavigationEnd);

    // 初始化状态
    setCurrentRoute(router.getState().currentRoute);
    setCanGoBack(router.getState().canGoBack);

    return () => {
      router.removeEventListener('beforeNavigate', handleNavigationStart);
      router.removeEventListener('afterNavigate', handleNavigationEnd);
      router.removeEventListener('navigationError', handleNavigationEnd);
      router.removeEventListener('routeChange', handleNavigationEnd);
    };
  }, []);

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.colors.surface }]}>
      {/* 状态栏配置 */}
      <StatusBar
        barStyle={theme.mode === 'dark' ? 'light-content' : 'dark-content'}
        backgroundColor={theme.colors.surface}
      />

      {/* 导航头部 */}
      {showHeader && (
        <NavigationHeader
          title={routeConfig?.title || currentRoute}
          canGoBack={canGoBack}
        />
      )}

      {/* 主要内容区域 */}
      <View style={styles.content}>
        {isLoading ? (
          <View style={[styles.loadingContainer, { backgroundColor: theme.colors.background }]}>
            <ActivityIndicator size="large" color={theme.colors.primary} />
            <Text style={[styles.loadingText, { color: theme.colors.textSecondary }]}>
              正在加载...
            </Text>
          </View>
        ) : (
          <PageRenderer currentRoute={currentRoute} />
        )}
      </View>

      {/* 底部Tab导航栏 */}
      {showTabBar && (
        <TabNavigator
          badges={{
            Todo: { count: 3 }, // 示例徽章
            Profile: { dot: true }, // 示例小红点
          }}
        />
      )}
    </SafeAreaView>
  );
};

/**
 * 增强版应用导航器主组件
 */
interface EnhancedAppNavigatorProps {
  initialRoute?: RouteName;
}

export const EnhancedAppNavigator: React.FC<EnhancedAppNavigatorProps> = ({
  initialRoute = 'Home',
}) => {
  const [isInitialized, setIsInitialized] = useState(false);

  // 初始化导航系统
  useEffect(() => {
    const initializeNavigation = async () => {
      try {
        // 注册所有路由
        router.registerRoutes(allRoutes);

        // 设置初始路由
        await router.navigate(initialRoute);

        setIsInitialized(true);
      } catch (error) {
        console.error('Navigation initialization error:', error);
        setIsInitialized(true); // 即使出错也要显示界面
      }
    };

    initializeNavigation();
  }, [initialRoute]);

  if (!isInitialized) {
    return (
      <View style={styles.initializingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.initializingText}>正在初始化导航系统...</Text>
      </View>
    );
  }

  return (
    <NavigationProvider initialRoute={initialRoute}>
      <NavigatorContent />
    </NavigationProvider>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    height: 56,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 16,
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
  backButton: {
    position: 'absolute',
    left: 16,
    fontSize: 16,
    fontWeight: '600',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    textAlign: 'center',
  },
  headerTitleWithBack: {
    marginLeft: 60, // 为返回按钮留出空间
  },
  content: {
    flex: 1,
  },
  pageContainer: {
    flex: 1,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  errorText: {
    fontSize: 16,
    textAlign: 'center',
  },
  initializingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F9FAFB',
  },
  initializingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#6B7280',
  },
});

export default EnhancedAppNavigator;
