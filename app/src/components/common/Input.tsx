/**
 * 通用输入框组件
 *
 * 这是一个功能丰富、高度可定制的输入框组件，提供：
 *
 * 主要特性：
 * 1. 标签支持 - 可显示输入框标题和必填标识
 * 2. 错误处理 - 支持错误信息显示和样式变化
 * 3. 帮助文本 - 可显示输入提示或说明信息
 * 4. 图标支持 - 支持左右两侧图标，右侧图标可点击
 * 5. 密码切换 - 内置密码显示/隐藏切换功能
 * 6. 样式定制 - 支持容器和输入框的自定义样式
 * 7. 引用转发 - 支持ref转发，便于外部控制焦点
 * 8. 完整继承 - 继承所有TextInput的原生属性
 *
 * 使用示例：
 * ```tsx
 * <Input
 *   label="邮箱地址"
 *   placeholder="请输入邮箱"
 *   value={email}
 *   onChangeText={setEmail}
 *   error={emailError}
 *   required
 * />
 * ```
 */

import React, { useState, forwardRef } from 'react';
import {
  View,           // 基础容器组件
  TextInput,      // 文本输入组件
  Text,           // 文本显示组件
  StyleSheet,     // 样式表
  TouchableOpacity, // 可点击容器组件
  TextInputProps, // TextInput属性类型
  ViewStyle,      // 视图样式类型
} from 'react-native';

/**
 * 输入框组件属性接口
 * 继承TextInput的所有属性，并添加自定义属性
 */
export interface InputProps extends TextInputProps {
  label?: string;                    // 输入框标签文本（可选）
  error?: string;                    // 错误信息文本（可选）
  helperText?: string;               // 帮助文本（可选）
  leftIcon?: React.ReactNode;        // 左侧图标（可选）
  rightIcon?: React.ReactNode;       // 右侧图标（可选）
  onRightIconPress?: () => void;     // 右侧图标点击事件（可选）
  containerStyle?: ViewStyle;        // 容器自定义样式（可选）
  inputStyle?: ViewStyle;            // 输入框自定义样式（可选）
  required?: boolean;                // 是否必填（可选，默认false）
  showPasswordToggle?: boolean;      // 是否显示密码切换按钮（可选，默认false）
}

const Input = forwardRef<TextInput, InputProps>(({
  label,
  error,
  helperText,
  leftIcon,
  rightIcon,
  onRightIconPress,
  containerStyle,
  inputStyle,
  required = false,
  showPasswordToggle = false,
  secureTextEntry,
  ...textInputProps
}, ref) => {
  const [isFocused, setIsFocused] = useState(false);
  const [isPasswordVisible, setIsPasswordVisible] = useState(false);

  // 处理焦点状态
  const handleFocus = (e: any) => {
    setIsFocused(true);
    textInputProps.onFocus?.(e);
  };

  const handleBlur = (e: any) => {
    setIsFocused(false);
    textInputProps.onBlur?.(e);
  };

  // 切换密码可见性
  const togglePasswordVisibility = () => {
    setIsPasswordVisible(!isPasswordVisible);
  };

  // 获取容器样式
  const getContainerStyle = () => {
    const baseStyle = [styles.container];
    
    if (isFocused) {
      baseStyle.push(styles.focused);
    }
    
    if (error) {
      baseStyle.push(styles.error);
    }
    
    if (textInputProps.editable === false) {
      baseStyle.push(styles.disabled);
    }
    
    return StyleSheet.flatten([baseStyle, containerStyle]);
  };

  // 获取输入框样式
  const getInputStyle = () => {
    const baseStyle = [styles.input];
    
    if (leftIcon) {
      baseStyle.push(styles.inputWithLeftIcon);
    }
    
    if (rightIcon || showPasswordToggle) {
      baseStyle.push(styles.inputWithRightIcon);
    }
    
    return StyleSheet.flatten([baseStyle, inputStyle]);
  };

  // 渲染右侧图标
  const renderRightIcon = () => {
    if (showPasswordToggle && secureTextEntry) {
      return (
        <TouchableOpacity
          style={styles.iconContainer}
          onPress={togglePasswordVisibility}
        >
          <Text style={styles.passwordToggle}>
            {isPasswordVisible ? '🙈' : '👁️'}
          </Text>
        </TouchableOpacity>
      );
    }
    
    if (rightIcon) {
      return (
        <TouchableOpacity
          style={styles.iconContainer}
          onPress={onRightIconPress}
          disabled={!onRightIconPress}
        >
          {rightIcon}
        </TouchableOpacity>
      );
    }
    
    return null;
  };

  return (
    <View style={styles.wrapper}>
      {/* 标签 */}
      {label && (
        <Text style={styles.label}>
          {label}
          {required && <Text style={styles.required}> *</Text>}
        </Text>
      )}
      
      {/* 输入框容器 */}
      <View style={getContainerStyle()}>
        {/* 左侧图标 */}
        {leftIcon && (
          <View style={styles.iconContainer}>
            {leftIcon}
          </View>
        )}
        
        {/* 输入框 */}
        <TextInput
          ref={ref}
          style={getInputStyle()}
          onFocus={handleFocus}
          onBlur={handleBlur}
          secureTextEntry={showPasswordToggle ? !isPasswordVisible : secureTextEntry}
          placeholderTextColor="#9CA3AF"
          {...textInputProps}
        />
        
        {/* 右侧图标 */}
        {renderRightIcon()}
      </View>
      
      {/* 错误信息或帮助文本 */}
      {error ? (
        <Text style={styles.errorText}>{error}</Text>
      ) : helperText ? (
        <Text style={styles.helperText}>{helperText}</Text>
      ) : null}
    </View>
  );
});

const styles = StyleSheet.create({
  wrapper: {
    marginBottom: 16,
  },
  label: {
    fontSize: 14,
    fontWeight: '500',
    color: '#374151',
    marginBottom: 6,
  },
  required: {
    color: '#EF4444',
  },
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#D1D5DB',
    borderRadius: 8,
    backgroundColor: '#FFFFFF',
    minHeight: 44,
  },
  focused: {
    borderColor: '#007AFF',
    borderWidth: 2,
  },
  error: {
    borderColor: '#EF4444',
  },
  disabled: {
    backgroundColor: '#F9FAFB',
    borderColor: '#E5E7EB',
  },
  input: {
    flex: 1,
    fontSize: 16,
    color: '#111827',
    paddingHorizontal: 12,
    paddingVertical: 10,
  },
  inputWithLeftIcon: {
    paddingLeft: 0,
  },
  inputWithRightIcon: {
    paddingRight: 0,
  },
  iconContainer: {
    paddingHorizontal: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },
  passwordToggle: {
    fontSize: 18,
  },
  errorText: {
    fontSize: 12,
    color: '#EF4444',
    marginTop: 4,
  },
  helperText: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 4,
  },
});

Input.displayName = 'Input';

export default Input;
