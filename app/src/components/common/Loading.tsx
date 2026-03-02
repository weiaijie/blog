/**
 * 通用加载组件
 */

import React from 'react';
import {
  View,
  ActivityIndicator,
  Text,
  StyleSheet,
  Modal,
  ViewStyle,
} from 'react-native';

// 加载组件类型
export type LoadingType = 'inline' | 'overlay' | 'fullscreen';

// 加载组件尺寸
export type LoadingSize = 'small' | 'medium' | 'large';

// 加载组件属性接口
export interface LoadingProps {
  visible?: boolean;
  type?: LoadingType;
  size?: LoadingSize;
  text?: string;
  color?: string;
  backgroundColor?: string;
  style?: ViewStyle;
  textStyle?: ViewStyle;
}

const Loading: React.FC<LoadingProps> = ({
  visible = true,
  type = 'inline',
  size = 'medium',
  text,
  color = '#007AFF',
  backgroundColor = 'rgba(0, 0, 0, 0.5)',
  style,
  textStyle,
}) => {
  // 获取指示器尺寸
  const getIndicatorSize = () => {
    switch (size) {
      case 'small':
        return 'small' as const;
      case 'large':
        return 'large' as const;
      default:
        return 'small' as const;
    }
  };

  // 获取容器样式
  const getContainerStyle = (): ViewStyle => {
    const baseStyle = [styles.container];
    
    switch (type) {
      case 'overlay':
        baseStyle.push(styles.overlay);
        break;
      case 'fullscreen':
        baseStyle.push(styles.fullscreen);
        break;
      default:
        baseStyle.push(styles.inline);
    }
    
    return StyleSheet.flatten([baseStyle, style]);
  };

  // 渲染加载内容
  const renderContent = () => (
    <View style={styles.content}>
      <ActivityIndicator
        size={getIndicatorSize()}
        color={color}
        style={styles.indicator}
      />
      {text && (
        <Text style={[styles.text, textStyle]}>
          {text}
        </Text>
      )}
    </View>
  );

  // 如果不可见，返回null
  if (!visible) {
    return null;
  }

  // 全屏或覆盖层模式使用Modal
  if (type === 'fullscreen' || type === 'overlay') {
    return (
      <Modal
        transparent
        visible={visible}
        animationType="fade"
        statusBarTranslucent
      >
        <View style={[getContainerStyle(), { backgroundColor }]}>
          {renderContent()}
        </View>
      </Modal>
    );
  }

  // 内联模式直接渲染
  return (
    <View style={getContainerStyle()}>
      {renderContent()}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  inline: {
    padding: 20,
  },
  overlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    zIndex: 1000,
  },
  fullscreen: {
    flex: 1,
  },
  content: {
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 24,
    minWidth: 120,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    elevation: 5,
  },
  indicator: {
    marginBottom: 12,
  },
  text: {
    fontSize: 14,
    color: '#374151',
    textAlign: 'center',
    fontWeight: '500',
  },
});

export default Loading;
