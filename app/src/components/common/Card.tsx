/**
 * 通用卡片组件
 */

import React from 'react';
import {
  View,
  StyleSheet,
  ViewStyle,
  TouchableOpacity,
} from 'react-native';

// 卡片变体类型
export type CardVariant = 'default' | 'elevated' | 'outlined' | 'filled';

// 卡片属性接口
export interface CardProps {
  children: React.ReactNode;
  variant?: CardVariant;
  onPress?: () => void;
  style?: ViewStyle;
  contentStyle?: ViewStyle;
  disabled?: boolean;
  testID?: string;
}

const Card: React.FC<CardProps> = ({
  children,
  variant = 'default',
  onPress,
  style,
  contentStyle,
  disabled = false,
  testID,
}) => {
  // 获取卡片样式
  const getCardStyle = (): ViewStyle => {
    const baseStyle = [styles.card, styles[`${variant}Card`]];
    
    if (disabled) {
      baseStyle.push(styles.disabled);
    }
    
    return StyleSheet.flatten([baseStyle, style]);
  };

  // 获取内容样式
  const getContentStyle = (): ViewStyle => {
    return StyleSheet.flatten([styles.content, contentStyle]);
  };

  // 如果有onPress，使用TouchableOpacity
  if (onPress) {
    return (
      <TouchableOpacity
        style={getCardStyle()}
        onPress={onPress}
        disabled={disabled}
        activeOpacity={0.7}
        testID={testID}
      >
        <View style={getContentStyle()}>
          {children}
        </View>
      </TouchableOpacity>
    );
  }

  // 否则使用普通View
  return (
    <View style={getCardStyle()} testID={testID}>
      <View style={getContentStyle()}>
        {children}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    borderRadius: 12,
    backgroundColor: '#FFFFFF',
  },
  content: {
    padding: 16,
  },
  
  // 变体样式
  defaultCard: {
    backgroundColor: '#FFFFFF',
  },
  elevatedCard: {
    backgroundColor: '#FFFFFF',
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  outlinedCard: {
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  filledCard: {
    backgroundColor: '#F9FAFB',
  },
  
  // 禁用样式
  disabled: {
    opacity: 0.6,
  },
});

export default Card;
