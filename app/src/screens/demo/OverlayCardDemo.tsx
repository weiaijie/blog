/**
 * 重叠卡片演示页面
 * 
 * 展示OverlayCard组件的使用示例
 */

import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { OverlayCard } from '../../components/common/OverlayCard';
import { useTheme } from '../../contexts/ThemeContext';

/**
 * 重叠卡片演示页面组件
 */
export const OverlayCardDemo: React.FC = () => {
  const { theme } = useTheme();

  const styles = StyleSheet.create({
    container: {
      flex: 1,
      backgroundColor: '#F5F5F5',
    },
    scrollContainer: {
      padding: 20,
      alignItems: 'center',
    },
    demoContent: {
      flex: 1,
      justifyContent: 'center',
      alignItems: 'center',
    },
    demoText: {
      fontSize: 16,
      color: '#333333',
      textAlign: 'center',
      lineHeight: 24,
      marginBottom: 20,
    },
    featureList: {
      alignSelf: 'stretch',
    },
    featureItem: {
      fontSize: 14,
      color: '#666666',
      marginBottom: 8,
      paddingLeft: 16,
    },
    spacing: {
      height: 40,
    },
  });

  return (
    <View style={styles.container}>
      <ScrollView 
        style={styles.scrollContainer} 
        showsVerticalScrollIndicator={false}
        contentContainerStyle={{ alignItems: 'center' }}
      >
        {/* 第一个卡片 - 表单示例 */}
        <OverlayCard title="请如实填写报名申请信息">
          <View style={styles.demoContent}>
            <View style={styles.featureList}>
              <Text style={styles.featureItem}>📱 手机号：137 6131 0088</Text>
              <Text style={styles.featureItem}>🎓 学段名称：小学</Text>
              <Text style={styles.featureItem}>📚 年级：三年级</Text>
              <Text style={styles.featureItem}>📍 地区：北京市</Text>
              <Text style={styles.featureItem}>🏫 学校：实验小学</Text>
            </View>
            <Text style={[styles.demoText, { fontSize: 12, color: '#999', marginTop: 20 }]}>
              * 标题栏部分遮挡容器上半部分
            </Text>
          </View>
        </OverlayCard>

        <View style={styles.spacing} />

        {/* 第二个卡片 - 文本域示例 */}
        <OverlayCard title="文本域字段名称">
          <View style={styles.demoContent}>
            <View style={{
              backgroundColor: '#F8F8F8',
              borderRadius: 4,
              padding: 12,
              minHeight: 100,
              borderWidth: 1,
              borderColor: '#E0E0E0',
            }}>
              <Text style={{ color: '#666', fontSize: 14, lineHeight: 20 }}>
                请在此输入详细信息...{'\n\n'}
                这里可以输入多行文本内容，
                比如个人简介、申请理由、
                特殊说明等信息。
              </Text>
            </View>
          </View>
        </OverlayCard>

        <View style={styles.spacing} />

        {/* 第三个卡片 */}
        <OverlayCard title="自定义标题">
          <View style={styles.demoContent}>
            <Text style={styles.demoText}>
              可以自定义标题内容
            </Text>
            <Text style={styles.demoText}>
              组件支持传入children内容，
              可以在卡片内放置任何React组件。
            </Text>
          </View>
        </OverlayCard>

        <View style={styles.spacing} />
      </ScrollView>
    </View>
  );
};

export default OverlayCardDemo;
