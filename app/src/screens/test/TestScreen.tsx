/**
 * 测试页面
 * 
 * 用于验证应用基本功能是否正常工作
 */

import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
} from 'react-native';
import { useTheme } from '../../contexts/ThemeContext';

/**
 * 测试页面组件
 */
export const TestScreen: React.FC = () => {
  const { theme, themeMode, toggleTheme } = useTheme();

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: theme.colors.background }]}
      contentContainerStyle={styles.content}
    >
      <Text style={[styles.title, { color: theme.colors.text }]}>
        应用测试页面
      </Text>

      <View style={[styles.section, { backgroundColor: theme.colors.surface }]}>
        <Text style={[styles.sectionTitle, { color: theme.colors.text }]}>
          主题系统测试
        </Text>
        <Text style={[styles.info, { color: theme.colors.textSecondary }]}>
          当前主题: {themeMode}
        </Text>
        <Text 
          style={[styles.link, { color: theme.colors.primary }]}
          onPress={toggleTheme}
        >
          点击切换主题
        </Text>
      </View>

      <View style={[styles.section, { backgroundColor: theme.colors.surface }]}>
        <Text style={[styles.sectionTitle, { color: theme.colors.text }]}>
          颜色测试
        </Text>
        <View style={styles.colorRow}>
          <View style={[styles.colorBox, { backgroundColor: theme.colors.primary }]} />
          <Text style={[styles.colorLabel, { color: theme.colors.textSecondary }]}>
            Primary
          </Text>
        </View>
        <View style={styles.colorRow}>
          <View style={[styles.colorBox, { backgroundColor: theme.colors.secondary }]} />
          <Text style={[styles.colorLabel, { color: theme.colors.textSecondary }]}>
            Secondary
          </Text>
        </View>
        <View style={styles.colorRow}>
          <View style={[styles.colorBox, { backgroundColor: theme.colors.success }]} />
          <Text style={[styles.colorLabel, { color: theme.colors.textSecondary }]}>
            Success
          </Text>
        </View>
        <View style={styles.colorRow}>
          <View style={[styles.colorBox, { backgroundColor: theme.colors.error }]} />
          <Text style={[styles.colorLabel, { color: theme.colors.textSecondary }]}>
            Error
          </Text>
        </View>
      </View>

      <View style={[styles.section, { backgroundColor: theme.colors.surface }]}>
        <Text style={[styles.sectionTitle, { color: theme.colors.text }]}>
          系统信息
        </Text>
        <Text style={[styles.info, { color: theme.colors.textSecondary }]}>
          React Native 学习测试应用
        </Text>
        <Text style={[styles.info, { color: theme.colors.textSecondary }]}>
          版本: 1.0.0
        </Text>
        <Text style={[styles.info, { color: theme.colors.textSecondary }]}>
          状态: 正常运行 ✅
        </Text>
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
  link: {
    fontSize: 14,
    textDecorationLine: 'underline',
    marginTop: 8,
  },
  colorRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  colorBox: {
    width: 20,
    height: 20,
    borderRadius: 4,
    marginRight: 12,
  },
  colorLabel: {
    fontSize: 14,
  },
});

export default TestScreen;
