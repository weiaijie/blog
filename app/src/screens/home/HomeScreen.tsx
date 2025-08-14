/**
 * 首页组件
 *
 * 这是应用的主页面，作为用户进入应用后看到的第一个页面，提供：
 *
 * 主要功能：
 * 1. 欢迎信息展示 - 向用户介绍应用的目的和功能
 * 2. 功能模块展示 - 以卡片形式展示应用的各个功能模块
 * 3. 快速入口 - 提供各功能模块的快速访问入口
 * 4. 登录功能演示 - 集成登录模态框，展示用户认证功能
 * 5. 学习指引 - 为React Native学习者提供功能演示
 *
 * 设计理念：
 * - 简洁明了的界面设计
 * - 功能模块化展示
 * - 良好的用户引导体验
 * - 响应式布局适配
 */

import React, { useState } from 'react';
import {
  View,           // 基础容器组件
  Text,           // 文本显示组件
  ScrollView,     // 可滚动容器组件
  StyleSheet,     // 样式表
  TouchableOpacity, // 可点击容器组件
  Alert,          // 系统弹窗组件
  Modal,          // 模态框组件
} from 'react-native';

import { Button } from '../../components/common';  // 自定义按钮组件
import LoginScreen from '../auth/LoginScreen';     // 登录页面组件

/**
 * 首页主组件
 */
const HomeScreen: React.FC = () => {
  // ==================== 状态管理 ====================

  // 登录模态框显示状态
  const [showLoginModal, setShowLoginModal] = useState(false);

  // ==================== 事件处理函数 ====================

  /**
   * 处理功能卡片点击事件
   *
   * @param featureName - 被点击的功能名称
   *
   * 功能：
   * 1. 如果是"用户认证"功能，显示登录模态框
   * 2. 其他功能显示开发中提示
   */
  const handleFeaturePress = (featureName: string) => {
    if (featureName === '用户认证') {
      setShowLoginModal(true);  // 显示登录模态框
    } else {
      // 其他功能暂时显示开发中提示
      Alert.alert('功能提示', `${featureName} 功能正在开发中...`);
    }
  };

  /**
   * 处理登录成功事件
   *
   * 功能：
   * 1. 关闭登录模态框
   * 2. 显示登录成功提示
   */
  const handleLoginSuccess = () => {
    setShowLoginModal(false);
    Alert.alert('登录成功', '欢迎使用RN学习应用！');
  };

  // ==================== 功能模块配置 ====================

  /**
   * 功能模块列表
   * 定义了首页展示的所有功能模块信息
   */
  const features = [
    { id: 1, title: '用户认证', description: '登录、注册、密码重置', icon: '🔐' },
    { id: 2, title: '数据存储', description: '本地存储、缓存管理', icon: '💾' },
    { id: 3, title: '网络请求', description: 'API调用、数据同步', icon: '🌐' },
    { id: 4, title: '设备功能', description: '相机、定位、通知', icon: '📱' },
    { id: 5, title: '主题切换', description: '明暗主题、个性化', icon: '🎨' },
    { id: 6, title: '性能优化', description: '内存管理、渲染优化', icon: '⚡' },
  ];

  return (
    <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
      <View style={styles.content}>
        {/* 欢迎区域 */}
        <View style={styles.welcomeSection}>
          <Text style={styles.welcomeTitle}>欢迎使用 RN 学习应用</Text>
          <Text style={styles.welcomeSubtitle}>
            这是一个用于学习 React Native 各种特性的测试应用
          </Text>
        </View>

        {/* 功能卡片区域 */}
        <View style={styles.featuresSection}>
          <Text style={styles.sectionTitle}>功能模块</Text>
          <View style={styles.featuresGrid}>
            {features.map((feature) => (
              <TouchableOpacity
                key={feature.id}
                style={styles.featureCard}
                onPress={() => handleFeaturePress(feature.title)}
                activeOpacity={0.7}
              >
                <Text style={styles.featureIcon}>{feature.icon}</Text>
                <Text style={styles.featureTitle}>{feature.title}</Text>
                <Text style={styles.featureDescription}>
                  {feature.description}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* 状态信息 */}
        <View style={styles.statusSection}>
          <Text style={styles.sectionTitle}>开发状态</Text>
          <View style={styles.statusCard}>
            <View style={styles.statusItem}>
              <Text style={styles.statusLabel}>项目架构</Text>
              <Text style={styles.statusValue}>✅ 已完成</Text>
            </View>
            <View style={styles.statusItem}>
              <Text style={styles.statusLabel}>导航系统</Text>
              <Text style={styles.statusValue}>🔄 开发中</Text>
            </View>
            <View style={styles.statusItem}>
              <Text style={styles.statusLabel}>状态管理</Text>
              <Text style={styles.statusValue}>⏳ 计划中</Text>
            </View>
            <View style={styles.statusItem}>
              <Text style={styles.statusLabel}>UI组件库</Text>
              <Text style={styles.statusValue}>⏳ 计划中</Text>
            </View>
          </View>
        </View>

        {/* 测试按钮区域 */}
        <View style={styles.testSection}>
          <Text style={styles.sectionTitle}>功能测试</Text>
          <View style={styles.testButtons}>
            <Button
              title="测试登录功能"
              onPress={() => setShowLoginModal(true)}
              variant="primary"
              style={styles.testButton}
            />
            <Button
              title="测试组件库"
              onPress={() => Alert.alert('组件库', '所有基础组件已实现！')}
              variant="outline"
              style={styles.testButton}
            />
          </View>
        </View>
      </View>

      {/* 登录模态框 */}
      <Modal
        visible={showLoginModal}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setShowLoginModal(false)}
      >
        <View style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <Button
              title="关闭"
              onPress={() => setShowLoginModal(false)}
              variant="ghost"
              size="small"
            />
          </View>
          <LoginScreen onLoginSuccess={handleLoginSuccess} />
        </View>
      </Modal>
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
  welcomeSection: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 20,
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
  welcomeTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#111827',
    marginBottom: 8,
    textAlign: 'center',
  },
  welcomeSubtitle: {
    fontSize: 16,
    color: '#6B7280',
    textAlign: 'center',
    lineHeight: 24,
  },
  featuresSection: {
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 16,
  },
  featuresGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  featureCard: {
    width: '48%',
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  featureIcon: {
    fontSize: 32,
    marginBottom: 8,
  },
  featureTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 4,
    textAlign: 'center',
  },
  featureDescription: {
    fontSize: 12,
    color: '#6B7280',
    textAlign: 'center',
    lineHeight: 16,
  },
  statusSection: {
    marginBottom: 20,
  },
  statusCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  statusItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  statusLabel: {
    fontSize: 14,
    color: '#374151',
    fontWeight: '500',
  },
  statusValue: {
    fontSize: 14,
    fontWeight: '600',
  },
  testSection: {
    marginBottom: 20,
  },
  testButtons: {
    gap: 12,
  },
  testButton: {
    marginBottom: 8,
  },
  modalContainer: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    padding: 16,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
});

export default HomeScreen;
