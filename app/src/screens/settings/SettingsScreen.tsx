/**
 * 设置页面组件
 *
 * 这是应用的设置页面，提供以下功能：
 *
 * 主要功能：
 * 1. 主题切换 - 在明亮和暗黑主题之间切换
 * 2. 功能开关 - 管理各种应用功能的开启/关闭状态
 * 3. 应用设置 - 语言、字体、缓存等基础设置
 * 4. 数据与隐私 - 隐私政策、用户协议等
 * 5. 开发者选项 - 调试模式、性能监控等开发工具
 * 6. 应用信息 - 版本号、构建信息等
 * 7. 重置功能 - 重置所有设置到默认状态
 *
 * 设计特点：
 * - 分组管理，结构清晰
 * - 支持主题切换，界面自适应
 * - 交互友好，提供即时反馈
 * - 设置项丰富，满足不同用户需求
 */

import React, { useState } from 'react';
import {
  View,           // 基础容器组件
  Text,           // 文本显示组件
  ScrollView,     // 可滚动容器组件
  StyleSheet,     // 样式表
  TouchableOpacity, // 可点击容器组件
  Alert,          // 系统弹窗组件
  Switch,         // 开关组件
} from 'react-native';

import { useTheme } from '../../contexts/ThemeContext'; // 主题管理Hook

/**
 * 设置页面主组件
 */
const SettingsScreen: React.FC = () => {
  // ==================== 主题管理 ====================

  // 从主题Context获取主题相关的状态和方法
  const { theme, isDark, toggleTheme } = useTheme();

  // ==================== 功能开关状态管理 ====================

  // 自动更新开关状态
  const [autoUpdate, setAutoUpdate] = useState(true);

  // 数据同步开关状态
  const [dataSync, setDataSync] = useState(false);

  // 崩溃报告开关状态
  const [crashReporting, setCrashReporting] = useState(true);

  // 使用分析开关状态
  const [analytics, setAnalytics] = useState(false);

  // ==================== 事件处理函数 ====================

  /**
   * 处理设置项点击事件
   *
   * @param settingName - 被点击的设置项名称
   *
   * 功能：显示开发中提示，在实际应用中应该导航到对应的设置页面
   */
  const handleSettingPress = (settingName: string) => {
    Alert.alert('设置', `${settingName} 功能正在开发中...`);
  };

  const settingSections = [
    {
      title: '应用设置',
      items: [
        { 
          id: 1, 
          title: '语言设置', 
          subtitle: '中文简体', 
          icon: '🌐',
          action: () => handleSettingPress('语言设置')
        },
        { 
          id: 2, 
          title: '字体大小', 
          subtitle: '标准', 
          icon: '🔤',
          action: () => handleSettingPress('字体大小')
        },
        { 
          id: 3, 
          title: '缓存管理', 
          subtitle: '清理应用缓存', 
          icon: '🗑️',
          action: () => handleSettingPress('缓存管理')
        },
      ]
    },
    {
      title: '数据与隐私',
      items: [
        { 
          id: 4, 
          title: '数据使用', 
          subtitle: '查看数据使用情况', 
          icon: '📊',
          action: () => handleSettingPress('数据使用')
        },
        { 
          id: 5, 
          title: '隐私政策', 
          subtitle: '了解隐私保护', 
          icon: '🔒',
          action: () => handleSettingPress('隐私政策')
        },
        { 
          id: 6, 
          title: '用户协议', 
          subtitle: '服务条款', 
          icon: '📄',
          action: () => handleSettingPress('用户协议')
        },
      ]
    },
    {
      title: '开发者选项',
      items: [
        { 
          id: 7, 
          title: '调试模式', 
          subtitle: '开发者调试工具', 
          icon: '🔧',
          action: () => handleSettingPress('调试模式')
        },
        { 
          id: 8, 
          title: '性能监控', 
          subtitle: '应用性能分析', 
          icon: '⚡',
          action: () => handleSettingPress('性能监控')
        },
        { 
          id: 9, 
          title: '日志查看', 
          subtitle: '查看应用日志', 
          icon: '📝',
          action: () => handleSettingPress('日志查看')
        },
      ]
    }
  ];

  return (
    <ScrollView style={[styles.container, { backgroundColor: theme.colors.background }]} showsVerticalScrollIndicator={false}>
      <View style={styles.content}>
        {/* 开关设置区域 */}
        <View style={[styles.switchSection, { backgroundColor: theme.colors.surface }]}>
          <Text style={[styles.sectionTitle, { color: theme.colors.text }]}>功能开关</Text>

          {/* 主题切换 */}
          <View style={[styles.switchItem, { borderBottomColor: theme.colors.border }]}>
            <View style={styles.switchLeft}>
              <Text style={styles.switchIcon}>{isDark ? '🌙' : '☀️'}</Text>
              <View>
                <Text style={[styles.switchTitle, { color: theme.colors.text }]}>深色主题</Text>
                <Text style={[styles.switchSubtitle, { color: theme.colors.textSecondary }]}>
                  {isDark ? '当前使用深色主题' : '当前使用浅色主题'}
                </Text>
              </View>
            </View>
            <Switch
              value={isDark}
              onValueChange={toggleTheme}
              trackColor={{ false: '#D1D5DB', true: theme.colors.primary }}
              thumbColor={isDark ? '#FFFFFF' : '#FFFFFF'}
            />
          </View>

          <View style={[styles.switchItem, { borderBottomColor: theme.colors.border }]}>
            <View style={styles.switchLeft}>
              <Text style={styles.switchIcon}>🔄</Text>
              <View>
                <Text style={[styles.switchTitle, { color: theme.colors.text }]}>自动更新</Text>
                <Text style={[styles.switchSubtitle, { color: theme.colors.textSecondary }]}>自动检查并下载更新</Text>
              </View>
            </View>
            <Switch
              value={autoUpdate}
              onValueChange={setAutoUpdate}
              trackColor={{ false: '#D1D5DB', true: theme.colors.primary }}
              thumbColor={autoUpdate ? '#FFFFFF' : '#FFFFFF'}
            />
          </View>

          <View style={[styles.switchItem, { borderBottomColor: theme.colors.border }]}>
            <View style={styles.switchLeft}>
              <Text style={styles.switchIcon}>☁️</Text>
              <View>
                <Text style={[styles.switchTitle, { color: theme.colors.text }]}>数据同步</Text>
                <Text style={[styles.switchSubtitle, { color: theme.colors.textSecondary }]}>同步数据到云端</Text>
              </View>
            </View>
            <Switch
              value={dataSync}
              onValueChange={setDataSync}
              trackColor={{ false: '#D1D5DB', true: theme.colors.primary }}
              thumbColor={dataSync ? '#FFFFFF' : '#FFFFFF'}
            />
          </View>

          <View style={styles.switchItem}>
            <View style={styles.switchLeft}>
              <Text style={styles.switchIcon}>🐛</Text>
              <View>
                <Text style={styles.switchTitle}>崩溃报告</Text>
                <Text style={styles.switchSubtitle}>发送崩溃信息帮助改进</Text>
              </View>
            </View>
            <Switch
              value={crashReporting}
              onValueChange={setCrashReporting}
              trackColor={{ false: '#D1D5DB', true: '#3B82F6' }}
              thumbColor={crashReporting ? '#FFFFFF' : '#FFFFFF'}
            />
          </View>

          <View style={styles.switchItem}>
            <View style={styles.switchLeft}>
              <Text style={styles.switchIcon}>📈</Text>
              <View>
                <Text style={styles.switchTitle}>使用分析</Text>
                <Text style={styles.switchSubtitle}>匿名使用数据分析</Text>
              </View>
            </View>
            <Switch
              value={analytics}
              onValueChange={setAnalytics}
              trackColor={{ false: '#D1D5DB', true: '#3B82F6' }}
              thumbColor={analytics ? '#FFFFFF' : '#FFFFFF'}
            />
          </View>
        </View>

        {/* 设置菜单区域 */}
        {settingSections.map((section, sectionIndex) => (
          <View key={sectionIndex} style={styles.menuSection}>
            <Text style={styles.sectionTitle}>{section.title}</Text>
            {section.items.map((item) => (
              <TouchableOpacity
                key={item.id}
                style={styles.menuItem}
                onPress={item.action}
                activeOpacity={0.7}
              >
                <View style={styles.menuLeft}>
                  <Text style={styles.menuIcon}>{item.icon}</Text>
                  <View style={styles.menuTextContainer}>
                    <Text style={styles.menuTitle}>{item.title}</Text>
                    <Text style={styles.menuSubtitle}>{item.subtitle}</Text>
                  </View>
                </View>
                <Text style={styles.menuArrow}>›</Text>
              </TouchableOpacity>
            ))}
          </View>
        ))}

        {/* 应用信息 */}
        <View style={styles.infoSection}>
          <Text style={styles.sectionTitle}>应用信息</Text>
          <View style={styles.infoItem}>
            <Text style={styles.infoLabel}>版本号</Text>
            <Text style={styles.infoValue}>1.0.0</Text>
          </View>
          <View style={styles.infoItem}>
            <Text style={styles.infoLabel}>构建号</Text>
            <Text style={styles.infoValue}>20250813</Text>
          </View>
          <View style={styles.infoItem}>
            <Text style={styles.infoLabel}>更新时间</Text>
            <Text style={styles.infoValue}>2025-08-13</Text>
          </View>
        </View>

        {/* 重置按钮 */}
        <TouchableOpacity 
          style={styles.resetButton}
          onPress={() => Alert.alert('确认', '确定要重置所有设置吗？此操作不可撤销。')}
        >
          <Text style={styles.resetButtonText}>重置所有设置</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  content: {
    padding: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 16,
  },
  switchSection: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  switchItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  switchLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  switchIcon: {
    fontSize: 20,
    marginRight: 12,
  },
  switchTitle: {
    fontSize: 16,
    color: '#374151',
    fontWeight: '500',
  },
  switchSubtitle: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 2,
  },
  menuSection: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  menuItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  menuLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  menuIcon: {
    fontSize: 20,
    marginRight: 12,
  },
  menuTextContainer: {
    flex: 1,
  },
  menuTitle: {
    fontSize: 16,
    color: '#374151',
    fontWeight: '500',
  },
  menuSubtitle: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 2,
  },
  menuArrow: {
    fontSize: 20,
    color: '#9CA3AF',
  },
  infoSection: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  infoItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  infoLabel: {
    fontSize: 14,
    color: '#374151',
  },
  infoValue: {
    fontSize: 14,
    color: '#6B7280',
    fontWeight: '500',
  },
  resetButton: {
    backgroundColor: '#EF4444',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    marginBottom: 20,
  },
  resetButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
});

export default SettingsScreen;
