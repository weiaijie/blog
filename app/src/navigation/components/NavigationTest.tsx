/**
 * 导航系统测试组件
 * 
 * 用于测试新导航系统的各项功能
 */

import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
} from 'react-native';
import { useNavigation, useRoute, useNavigationState } from '../NavigationContext';
import { useTheme } from '../../contexts/ThemeContext';

/**
 * 导航测试组件
 */
export const NavigationTest: React.FC = () => {
  const { theme } = useTheme();
  const navigation = useNavigation();
  const route = useRoute();
  const { state, canGoBack, canGoForward } = useNavigationState();

  const handleNavigate = async (routeName: string) => {
    try {
      await navigation.navigate(routeName as any);
    } catch (error) {
      console.error('Navigation error:', error);
    }
  };

  const handleGoBack = async () => {
    try {
      await navigation.goBack();
    } catch (error) {
      console.error('Go back error:', error);
    }
  };

  const handleGoForward = async () => {
    try {
      await navigation.goForward();
    } catch (error) {
      console.error('Go forward error:', error);
    }
  };

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: theme.colors.background }]}
      contentContainerStyle={styles.content}
    >
      <Text style={[styles.title, { color: theme.colors.text }]}>
        导航系统测试
      </Text>

      {/* 当前路由信息 */}
      <View style={[styles.section, { backgroundColor: theme.colors.surface }]}>
        <Text style={[styles.sectionTitle, { color: theme.colors.text }]}>
          当前路由信息
        </Text>
        <Text style={[styles.info, { color: theme.colors.textSecondary }]}>
          路由名称: {route.name}
        </Text>
        <Text style={[styles.info, { color: theme.colors.textSecondary }]}>
          路由参数: {JSON.stringify(route.params || {}, null, 2)}
        </Text>
      </View>

      {/* 导航状态 */}
      <View style={[styles.section, { backgroundColor: theme.colors.surface }]}>
        <Text style={[styles.sectionTitle, { color: theme.colors.text }]}>
          导航状态
        </Text>
        <Text style={[styles.info, { color: theme.colors.textSecondary }]}>
          可以返回: {canGoBack ? '是' : '否'}
        </Text>
        <Text style={[styles.info, { color: theme.colors.textSecondary }]}>
          可以前进: {canGoForward ? '是' : '否'}
        </Text>
        <Text style={[styles.info, { color: theme.colors.textSecondary }]}>
          历史记录数量: {state.history.length}
        </Text>
      </View>

      {/* 导航操作按钮 */}
      <View style={[styles.section, { backgroundColor: theme.colors.surface }]}>
        <Text style={[styles.sectionTitle, { color: theme.colors.text }]}>
          导航操作
        </Text>
        
        <View style={styles.buttonRow}>
          <TouchableOpacity
            style={[
              styles.button,
              { backgroundColor: theme.colors.primary },
              !canGoBack && styles.disabledButton,
            ]}
            onPress={handleGoBack}
            disabled={!canGoBack}
          >
            <Text style={[styles.buttonText, { color: theme.colors.surface }]}>
              返回
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[
              styles.button,
              { backgroundColor: theme.colors.primary },
              !canGoForward && styles.disabledButton,
            ]}
            onPress={handleGoForward}
            disabled={!canGoForward}
          >
            <Text style={[styles.buttonText, { color: theme.colors.surface }]}>
              前进
            </Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* 页面导航按钮 */}
      <View style={[styles.section, { backgroundColor: theme.colors.surface }]}>
        <Text style={[styles.sectionTitle, { color: theme.colors.text }]}>
          页面导航
        </Text>
        
        <View style={styles.buttonGrid}>
          {['Home', 'Todo', 'Profile', 'Settings'].map((routeName) => (
            <TouchableOpacity
              key={routeName}
              style={[
                styles.button,
                { backgroundColor: theme.colors.secondary },
                route.name === routeName && styles.activeButton,
              ]}
              onPress={() => handleNavigate(routeName)}
            >
              <Text style={[styles.buttonText, { color: theme.colors.surface }]}>
                {routeName}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      {/* 历史记录 */}
      <View style={[styles.section, { backgroundColor: theme.colors.surface }]}>
        <Text style={[styles.sectionTitle, { color: theme.colors.text }]}>
          导航历史
        </Text>
        {state.history.map((item, index) => (
          <View key={index} style={styles.historyItem}>
            <Text style={[styles.historyText, { color: theme.colors.textSecondary }]}>
              {index + 1}. {item.route} - {new Date(item.timestamp).toLocaleTimeString()}
            </Text>
          </View>
        ))}
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  content: {
    padding: 16,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 20,
  },
  section: {
    padding: 16,
    marginBottom: 16,
    borderRadius: 8,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 12,
  },
  info: {
    fontSize: 14,
    marginBottom: 4,
  },
  buttonRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginTop: 12,
  },
  buttonGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    marginTop: 12,
  },
  button: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 6,
    marginBottom: 8,
    minWidth: 80,
    alignItems: 'center',
  },
  disabledButton: {
    opacity: 0.5,
  },
  activeButton: {
    opacity: 0.8,
  },
  buttonText: {
    fontSize: 14,
    fontWeight: '600',
  },
  historyItem: {
    paddingVertical: 4,
  },
  historyText: {
    fontSize: 12,
  },
});

export default NavigationTest;
