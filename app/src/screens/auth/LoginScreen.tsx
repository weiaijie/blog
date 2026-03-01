/**
 * 登录页面组件
 *
 * 这是一个完整的用户登录页面，提供以下功能：
 *
 * 主要功能：
 * 1. 用户登录表单 - 邮箱和密码输入
 * 2. 表单验证 - 实时验证输入数据的有效性
 * 3. 错误处理 - 显示登录错误和验证错误信息
 * 4. 加载状态 - 登录过程中的加载指示
 * 5. 键盘适配 - 自动适配键盘弹出，避免遮挡
 * 6. 响应式设计 - 适配不同屏幕尺寸
 * 7. 用户体验优化 - 流畅的交互和反馈
 *
 * 技术特点：
 * - 使用React Hooks进行状态管理
 * - 集成自定义Input和Button组件
 * - 支持键盘避让功能
 * - 完整的表单验证逻辑
 * - 与Redux状态管理集成
 */

import React, { useState } from 'react';
import {
  View,               // 基础容器组件
  Text,               // 文本显示组件
  ScrollView,         // 可滚动容器组件
  StyleSheet,         // 样式表
  Alert,              // 系统弹窗组件
  KeyboardAvoidingView, // 键盘避让容器组件
  Platform,           // 平台检测工具
} from 'react-native';

import { Button, Input, Card, Loading } from '../../components/common'; // 自定义通用组件
import { useAuthContext } from '../../contexts/AuthContext'; // 认证状态管理Hook

import { useNavigation } from '@react-navigation/native';
import type { AuthStackScreenProps } from '../../navigation/navigation.types';

/**
 * 登录页面组件属性接口
 */
interface LoginScreenProps {
  onLoginSuccess?: () => void;     // 登录成功回调函数（可选）
  onSwitchToRegister?: () => void; // 切换到注册页面回调函数（可选）
}

const LoginScreen: React.FC<LoginScreenProps> = ({
  onLoginSuccess,
  onSwitchToRegister
}) => {
  // React Navigation导航对象
  const navigation = useNavigation<AuthStackScreenProps<'Login'>['navigation']>();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [emailError, setEmailError] = useState('');
  const [passwordError, setPasswordError] = useState('');

  const { login, loading, error } = useAuthContext();

  // 验证邮箱格式
  const validateEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!email) {
      setEmailError('请输入邮箱地址');
      return false;
    }
    if (!emailRegex.test(email)) {
      setEmailError('请输入有效的邮箱地址');
      return false;
    }
    setEmailError('');
    return true;
  };

  // 验证密码
  const validatePassword = (password: string): boolean => {
    if (!password) {
      setPasswordError('请输入密码');
      return false;
    }
    if (password.length < 6) {
      setPasswordError('密码长度至少6位');
      return false;
    }
    setPasswordError('');
    return true;
  };

  // 处理登录
  const handleLogin = async () => {
    const isEmailValid = validateEmail(email);
    const isPasswordValid = validatePassword(password);

    if (!isEmailValid || !isPasswordValid) {
      return;
    }

    try {
      console.log('开始登录，邮箱:', email, '密码:', password);
      const result = await login(email, password);
      console.log('登录结果:', result);

      if (result.success) {
        console.log('登录成功，调用回调函数');
        // 登录成功，直接调用回调函数
        if (onLoginSuccess) {
          onLoginSuccess();
        }
      } else {
        Alert.alert('登录失败', result.error || '登录过程中发生错误');
      }
    } catch (err) {
      console.error('登录异常:', err);
      Alert.alert('登录失败', '网络错误，请稍后重试');
    }
  };

  // 处理忘记密码
  const handleForgotPassword = () => {
    Alert.alert('忘记密码', '密码重置功能正在开发中...');
  };

  // 处理注册
  const handleRegister = () => {
    if (onSwitchToRegister) {
      onSwitchToRegister();
    } else if (navigation) {
      // 使用React Navigation导航到注册页面
      navigation.navigate('Register');
    } else {
      Alert.alert('注册账户', '注册功能正在开发中...');
    }
  };

  // 快速登录（演示用）
  const handleQuickLogin = () => {
    setEmail('learner@example.com');
    setPassword('123456');
    setEmailError('');
    setPasswordError('');
  };

  return (
    <KeyboardAvoidingView 
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView 
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        keyboardShouldPersistTaps="handled"
      >
        {/* 标题区域 */}
        <View style={styles.header}>
          <Text style={styles.title}>欢迎回来</Text>
          <Text style={styles.subtitle}>登录您的账户继续学习</Text>
        </View>

        {/* 登录表单 */}
        <Card variant="elevated" style={styles.formCard}>
          <Input
            label="邮箱地址"
            placeholder="请输入邮箱地址"
            value={email}
            onChangeText={setEmail}
            error={emailError}
            keyboardType="email-address"
            autoCapitalize="none"
            autoCorrect={false}
            leftIcon={<Text style={styles.inputIcon}>📧</Text>}
            required
          />

          <Input
            label="密码"
            placeholder="请输入密码"
            value={password}
            onChangeText={setPassword}
            error={passwordError}
            secureTextEntry
            showPasswordToggle
            leftIcon={<Text style={styles.inputIcon}>🔒</Text>}
            required
          />

          {/* 错误信息 */}
          {error && (
            <Text style={styles.errorMessage}>{error}</Text>
          )}

          {/* 登录按钮 */}
          <Button
            title="登录"
            onPress={handleLogin}
            loading={loading}
            fullWidth
            style={styles.loginButton}
          />

          {/* 忘记密码 */}
          <Button
            title="忘记密码？"
            onPress={handleForgotPassword}
            variant="ghost"
            size="small"
            style={styles.forgotButton}
          />
        </Card>

        {/* 快速登录提示 */}
        <Card variant="outlined" style={styles.demoCard}>
          <Text style={styles.demoTitle}>演示账户</Text>
          <Text style={styles.demoText}>
            邮箱: learner@example.com{'\n'}
            密码: 123456
          </Text>
          <Button
            title="快速填充"
            onPress={handleQuickLogin}
            variant="outline"
            size="small"
            style={styles.demoButton}
          />
        </Card>

        {/* 注册链接 */}
        <View style={styles.footer}>
          <Text style={styles.footerText}>还没有账户？</Text>
          <Button
            title="立即注册"
            onPress={handleRegister}
            variant="ghost"
            size="small"
          />
        </View>
      </ScrollView>

      {/* 全屏加载 */}
      <Loading
        visible={loading}
        type="overlay"
        text="正在登录..."
      />
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    padding: 20,
    justifyContent: 'center',
  },
  header: {
    alignItems: 'center',
    marginBottom: 32,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#111827',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#6B7280',
    textAlign: 'center',
  },
  formCard: {
    marginBottom: 20,
  },
  inputIcon: {
    fontSize: 16,
  },
  errorMessage: {
    color: '#EF4444',
    fontSize: 14,
    textAlign: 'center',
    marginBottom: 16,
    padding: 12,
    backgroundColor: '#FEF2F2',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#FECACA',
  },
  loginButton: {
    marginTop: 8,
  },
  forgotButton: {
    marginTop: 8,
  },
  demoCard: {
    marginBottom: 20,
    alignItems: 'center',
  },
  demoTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 8,
  },
  demoText: {
    fontSize: 14,
    color: '#6B7280',
    textAlign: 'center',
    marginBottom: 12,
    lineHeight: 20,
  },
  demoButton: {
    minWidth: 100,
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 20,
  },
  footerText: {
    fontSize: 14,
    color: '#6B7280',
    marginRight: 8,
  },
});

export default LoginScreen;
