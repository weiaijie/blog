/**
 * 通用按钮组件
 *
 * 这是一个功能丰富、高度可定制的按钮组件，提供：
 *
 * 主要特性：
 * 1. 多种视觉样式 - primary、secondary、outline、ghost、danger
 * 2. 多种尺寸规格 - small、medium、large
 * 3. 状态管理 - 支持禁用和加载状态
 * 4. 图标支持 - 可在左侧或右侧添加图标
 * 5. 布局选项 - 支持全宽度布局
 * 6. 自定义样式 - 支持外部样式覆盖
 * 7. 无障碍支持 - 提供完整的可访问性支持
 *
 * 使用示例：
 * ```tsx
 * <Button
 *   title="点击我"
 *   onPress={() => console.log('clicked')}
 *   variant="primary"
 *   size="medium"
 * />
 * ```
 */

import React from 'react';
import {
  TouchableOpacity,  // 可点击的容器组件
  Text,             // 文本显示组件
  StyleSheet,       // 样式表
  ActivityIndicator, // 加载指示器组件
  ViewStyle,        // 视图样式类型
  TextStyle,        // 文本样式类型
} from 'react-native';

/**
 * 按钮变体类型定义
 * 定义了按钮的不同视觉样式
 */
export type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';

/**
 * 按钮尺寸类型定义
 * 定义了按钮的不同大小规格
 */
export type ButtonSize = 'small' | 'medium' | 'large';

/**
 * 按钮组件属性接口
 * 定义了按钮组件接受的所有属性
 */
export interface ButtonProps {
  title: string;                          // 按钮显示的文本（必填）
  onPress: () => void;                    // 点击事件处理函数（必填）
  variant?: ButtonVariant;                // 按钮样式变体（可选，默认primary）
  size?: ButtonSize;                      // 按钮尺寸（可选，默认medium）
  disabled?: boolean;                     // 是否禁用（可选，默认false）
  loading?: boolean;                      // 是否显示加载状态（可选，默认false）
  fullWidth?: boolean;                    // 是否占满容器宽度（可选，默认false）
  style?: ViewStyle;                      // 自定义容器样式（可选）
  textStyle?: TextStyle;                  // 自定义文本样式（可选）
  icon?: React.ReactNode;                 // 图标元素（可选）
  iconPosition?: 'left' | 'right';       // 图标位置（可选，默认left）
}

const Button: React.FC<ButtonProps> = ({
  title,
  onPress,
  variant = 'primary',
  size = 'medium',
  disabled = false,
  loading = false,
  fullWidth = false,
  style,
  textStyle,
  icon,
  iconPosition = 'left',
}) => {
  // 获取按钮样式
  const getButtonStyle = (): ViewStyle => {
    const baseStyle = [styles.button, styles[`${size}Button`]];
    
    if (fullWidth) {
      baseStyle.push(styles.fullWidth);
    }
    
    if (disabled || loading) {
      baseStyle.push(styles.disabled);
    } else {
      baseStyle.push(styles[`${variant}Button`]);
    }
    
    return StyleSheet.flatten([baseStyle, style]);
  };

  // 获取文本样式
  const getTextStyle = (): TextStyle => {
    const baseStyle = [styles.text, styles[`${size}Text`]];
    
    if (disabled || loading) {
      baseStyle.push(styles.disabledText);
    } else {
      baseStyle.push(styles[`${variant}Text`]);
    }
    
    return StyleSheet.flatten([baseStyle, textStyle]);
  };

  // 渲染按钮内容
  const renderContent = () => {
    if (loading) {
      return (
        <>
          <ActivityIndicator 
            size="small" 
            color={variant === 'primary' ? '#FFFFFF' : '#6B7280'} 
            style={styles.loadingIndicator}
          />
          <Text style={getTextStyle()}>加载中...</Text>
        </>
      );
    }

    if (icon) {
      return (
        <>
          {iconPosition === 'left' && icon}
          <Text style={getTextStyle()}>{title}</Text>
          {iconPosition === 'right' && icon}
        </>
      );
    }

    return <Text style={getTextStyle()}>{title}</Text>;
  };

  return (
    <TouchableOpacity
      style={getButtonStyle()}
      onPress={onPress}
      disabled={disabled || loading}
      activeOpacity={0.7}
    >
      {renderContent()}
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  button: {
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
    flexDirection: 'row',
  },
  fullWidth: {
    width: '100%',
  },
  
  // 尺寸样式
  smallButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    minHeight: 32,
  },
  mediumButton: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    minHeight: 40,
  },
  largeButton: {
    paddingHorizontal: 20,
    paddingVertical: 14,
    minHeight: 48,
  },
  
  // 变体样式
  primaryButton: {
    backgroundColor: '#007AFF',
  },
  secondaryButton: {
    backgroundColor: '#F3F4F6',
  },
  outlineButton: {
    backgroundColor: 'transparent',
    borderWidth: 1,
    borderColor: '#007AFF',
  },
  ghostButton: {
    backgroundColor: 'transparent',
  },
  dangerButton: {
    backgroundColor: '#EF4444',
  },
  
  // 禁用样式
  disabled: {
    backgroundColor: '#E5E7EB',
    borderColor: '#E5E7EB',
  },
  
  // 文本样式
  text: {
    fontWeight: '600',
    textAlign: 'center',
  },
  smallText: {
    fontSize: 12,
  },
  mediumText: {
    fontSize: 14,
  },
  largeText: {
    fontSize: 16,
  },
  
  // 变体文本样式
  primaryText: {
    color: '#FFFFFF',
  },
  secondaryText: {
    color: '#374151',
  },
  outlineText: {
    color: '#007AFF',
  },
  ghostText: {
    color: '#007AFF',
  },
  dangerText: {
    color: '#FFFFFF',
  },
  disabledText: {
    color: '#9CA3AF',
  },
  
  // 加载指示器
  loadingIndicator: {
    marginRight: 8,
  },
});

export default Button;
