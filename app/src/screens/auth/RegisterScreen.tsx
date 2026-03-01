/**
 * 注册页面组件
 *
 * 这是一个完整的用户注册页面，提供以下功能：
 *
 * 主要功能：
 * 1. 用户注册表单 - 邮箱、用户名、密码输入
 * 2. 表单验证 - 实时验证输入数据的有效性
 * 3. 错误处理 - 显示注册错误和验证错误信息
 * 4. 加载状态 - 注册过程中的加载指示
 * 5. 键盘适配 - 自动适配键盘弹出，避免遮挡
 * 6. 响应式设计 - 适配不同屏幕尺寸
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  Alert,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';

import { Button, Input, Card } from '../../components/common';
import { useAuthContext } from '../../contexts/AuthContext';
import { useTheme } from '../../contexts/ThemeContext';
import { useNavigation } from '@react-navigation/native';
import type { AuthStackScreenProps } from '../../navigation/navigation.types';

/**
 * 注册页面组件属性接口
 */
interface RegisterScreenProps {
  onRegisterSuccess?: () => void;  // 注册成功回调函数（可选）
  onSwitchToLogin?: () => void;    // 切换到登录页面回调函数（可选）
}

const RegisterScreen: React.FC<RegisterScreenProps> = ({
  onRegisterSuccess,
  onSwitchToLogin
}) => {
  const { theme } = useTheme();
  const navigation = useNavigation<AuthStackScreenProps<'Register'>['navigation']>();
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  
  // 错误状态
  const [emailError, setEmailError] = useState('');
  const [usernameError, setUsernameError] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [confirmPasswordError, setConfirmPasswordError] = useState('');

  const { register, loading, error } = useAuthContext();

  // 邮箱验证
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

  // 用户名验证
  const validateUsername = (username: string): boolean => {
    if (!username) {
      setUsernameError('请输入用户名');
      return false;
    }
    if (username.length < 3) {
      setUsernameError('用户名至少需要3个字符');
      return false;
    }
    if (username.length > 20) {
      setUsernameError('用户名不能超过20个字符');
      return false;
    }
    setUsernameError('');
    return true;
  };

  // 密码验证
  const validatePassword = (password: string): boolean => {
    if (!password) {
      setPasswordError('请输入密码');
      return false;
    }
    if (password.length < 6) {
      setPasswordError('密码至少需要6个字符');
      return false;
    }
    setPasswordError('');
    return true;
  };

  // 确认密码验证
  const validateConfirmPassword = (confirmPassword: string): boolean => {
    if (!confirmPassword) {
      setConfirmPasswordError('请确认密码');
      return false;
    }
    if (confirmPassword !== password) {
      setConfirmPasswordError('两次输入的密码不一致');
      return false;
    }
    setConfirmPasswordError('');
    return true;
  };

  // 处理注册
  const handleRegister = async () => {
    // 验证所有字段
    const isEmailValid = validateEmail(email);
    const isUsernameValid = validateUsername(username);
    const isPasswordValid = validatePassword(password);
    const isConfirmPasswordValid = validateConfirmPassword(confirmPassword);

    if (!isEmailValid || !isUsernameValid || !isPasswordValid || !isConfirmPasswordValid) {
      return;
    }

    try {
      const result = await register({
        email,
        username,
        password,
        firstName: firstName || undefined,
        lastName: lastName || undefined,
      });

      if (result.success) {
        Alert.alert(
          '注册成功',
          '欢迎加入我们！',
          [
            {
              text: '确定',
              onPress: () => {
                if (onRegisterSuccess) {
                  onRegisterSuccess();
                }
              },
            },
          ]
        );
      } else {
        Alert.alert('注册失败', result.error || '注册过程中发生错误');
      }
    } catch (error) {
      Alert.alert('注册失败', '网络错误，请稍后重试');
    }
  };

  return (
    <KeyboardAvoidingView
      style={[styles.container, { backgroundColor: theme.colors.background }]}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        keyboardShouldPersistTaps="handled"
      >
        <Card style={styles.card}>
          <Text style={[styles.title, { color: theme.colors.text }]}>
            创建账户
          </Text>
          <Text style={[styles.subtitle, { color: theme.colors.textSecondary }]}>
            填写以下信息完成注册
          </Text>

          {/* 全局错误信息 */}
          {error && (
            <Text style={[styles.errorText, { color: theme.colors.error }]}>
              {error}
            </Text>
          )}

          {/* 邮箱输入 */}
          <Input
            label="邮箱地址 *"
            value={email}
            onChangeText={(text) => {
              setEmail(text);
              if (emailError) validateEmail(text);
            }}
            onBlur={() => validateEmail(email)}
            placeholder="请输入邮箱地址"
            keyboardType="email-address"
            autoCapitalize="none"
            error={emailError}
          />

          {/* 用户名输入 */}
          <Input
            label="用户名 *"
            value={username}
            onChangeText={(text) => {
              setUsername(text);
              if (usernameError) validateUsername(text);
            }}
            onBlur={() => validateUsername(username)}
            placeholder="请输入用户名"
            autoCapitalize="none"
            error={usernameError}
          />

          {/* 姓名输入 */}
          <View style={styles.nameRow}>
            <Input
              label="名字"
              value={firstName}
              onChangeText={setFirstName}
              placeholder="名字"
              style={styles.nameInput}
            />
            <Input
              label="姓氏"
              value={lastName}
              onChangeText={setLastName}
              placeholder="姓氏"
              style={styles.nameInput}
            />
          </View>

          {/* 密码输入 */}
          <Input
            label="密码 *"
            value={password}
            onChangeText={(text) => {
              setPassword(text);
              if (passwordError) validatePassword(text);
              if (confirmPassword && confirmPasswordError) {
                validateConfirmPassword(confirmPassword);
              }
            }}
            onBlur={() => validatePassword(password)}
            placeholder="请输入密码"
            secureTextEntry
            error={passwordError}
          />

          {/* 确认密码输入 */}
          <Input
            label="确认密码 *"
            value={confirmPassword}
            onChangeText={(text) => {
              setConfirmPassword(text);
              if (confirmPasswordError) validateConfirmPassword(text);
            }}
            onBlur={() => validateConfirmPassword(confirmPassword)}
            placeholder="请再次输入密码"
            secureTextEntry
            error={confirmPasswordError}
          />

          {/* 注册按钮 */}
          <Button
            title="注册"
            onPress={handleRegister}
            loading={loading}
            style={styles.registerButton}
          />

          {/* 切换到登录 */}
          <View style={styles.footer}>
            <Text style={[styles.footerText, { color: theme.colors.textSecondary }]}>
              已有账户？
            </Text>
            <Text
              style={[styles.linkText, { color: theme.colors.primary }]}
              onPress={() => {
                if (onSwitchToLogin) {
                  onSwitchToLogin();
                } else if (navigation) {
                  navigation.navigate('Login');
                }
              }}
            >
              立即登录
            </Text>
          </View>
        </Card>
      </ScrollView>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    justifyContent: 'center',
    padding: 20,
  },
  card: {
    padding: 24,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    textAlign: 'center',
    marginBottom: 32,
  },
  errorText: {
    fontSize: 14,
    textAlign: 'center',
    marginBottom: 16,
    padding: 12,
    backgroundColor: 'rgba(239, 68, 68, 0.1)',
    borderRadius: 8,
  },
  nameRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  nameInput: {
    flex: 1,
    marginHorizontal: 4,
  },
  registerButton: {
    marginTop: 24,
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
    marginRight: 8,
  },
  linkText: {
    fontSize: 14,
    fontWeight: '600',
  },
});

export default RegisterScreen;
