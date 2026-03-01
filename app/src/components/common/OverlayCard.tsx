/**
 * 带有重叠标题的卡片组件
 * 
 * 创建一个白色容器，顶部有蓝色标题栏，标题栏会部分遮挡容器
 */

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

interface OverlayCardProps {
  title: string;
  children?: React.ReactNode;
  containerStyle?: any;
  titleStyle?: any;
}

/**
 * 重叠标题卡片组件
 */
export const OverlayCard: React.FC<OverlayCardProps> = ({ 
  title, 
  children, 
  containerStyle,
  titleStyle 
}) => {
  const styles = StyleSheet.create({
    wrapper: {
      position: 'relative',
      marginTop: 26, // 为标题栏留出空间（53/2 = 26.5，向下取整）
    },
    container: {
      width: 343,
      height: 295,
      backgroundColor: '#FFFFFF',
      borderRadius: 6,
      shadowColor: '#000',
      shadowOffset: {
        width: 0,
        height: 2,
      },
      shadowOpacity: 0.1,
      shadowRadius: 3.84,
      elevation: 5,
      paddingTop: 40, // 为标题栏留出内部空间
      paddingHorizontal: 16,
      paddingBottom: 16,
    },
    titleBar: {
      position: 'absolute',
      top: -26, // 向上偏移一半高度，让标题栏遮挡容器上半部分
      left: 0,
      width: 164,
      height: 53,
      backgroundColor: '#007CBC',
      borderRadius: 6,
      justifyContent: 'center',
      alignItems: 'center',
      zIndex: 10, // 确保标题栏在容器之上
    },
    titleText: {
      color: '#FFFFFF',
      fontSize: 14,
      fontWeight: '500',
      textAlign: 'center',
    },
    content: {
      flex: 1,
    },
  });

  return (
    <View style={styles.wrapper}>
      <View style={[styles.container, containerStyle]}>
        {/* 标题栏 - 绝对定位，部分遮挡容器 */}
        <View style={styles.titleBar}>
          <Text style={[styles.titleText, titleStyle]}>{title}</Text>
        </View>
        
        {/* 内容区域 */}
        <View style={styles.content}>
          {children}
        </View>
      </View>
    </View>
  );
};

export default OverlayCard;
