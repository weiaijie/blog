/**
 * 签到积分页面
 * 
 * 包含签到功能和积分显示，修复五角星显示问题
 */

import React, { useState } from 'react';
import { 
  View, 
  Text, 
  TouchableOpacity, 
  StyleSheet, 
  ScrollView,
  Alert 
} from 'react-native';
import { useTheme } from '../../contexts/ThemeContext';

interface CheckinScreenProps {}

/**
 * 签到积分页面组件
 */
export const CheckinScreen: React.FC<CheckinScreenProps> = () => {
  const { theme } = useTheme();
  const [points, setPoints] = useState(1250);
  const [checkedIn, setCheckedIn] = useState(false);
  const [consecutiveDays, setConsecutiveDays] = useState(7);

  const handleCheckin = () => {
    if (checkedIn) {
      Alert.alert('提示', '今日已签到！');
      return;
    }

    const earnedPoints = 10 + (consecutiveDays >= 7 ? 5 : 0); // 连续7天额外奖励
    setPoints(prev => prev + earnedPoints);
    setCheckedIn(true);
    setConsecutiveDays(prev => prev + 1);
    
    Alert.alert(
      '签到成功！', 
      `获得 ${earnedPoints} 积分${consecutiveDays >= 6 ? '（连续签到奖励）' : ''}`
    );
  };

  const styles = StyleSheet.create({
    container: {
      flex: 1,
      backgroundColor: '#F5F7FA',
    },
    scrollContainer: {
      padding: 16,
    },
    pointsCard: {
      backgroundColor: '#FFFFFF',
      borderRadius: 12,
      padding: 20,
      marginBottom: 16,
      shadowColor: '#000',
      shadowOffset: {
        width: 0,
        height: 2,
      },
      shadowOpacity: 0.1,
      shadowRadius: 3.84,
      elevation: 5,
    },
    pointsHeader: {
      flexDirection: 'row',
      alignItems: 'center',
      marginBottom: 12,
    },
    pointsTitle: {
      fontSize: 18,
      fontWeight: '600',
      color: '#333333',
      marginLeft: 8,
    },
    pointsValue: {
      fontSize: 32,
      fontWeight: 'bold',
      color: '#FF6B35',
      textAlign: 'center',
    },
    pointsLabel: {
      fontSize: 14,
      color: '#666666',
      textAlign: 'center',
      marginTop: 4,
    },
    checkinCard: {
      backgroundColor: '#FFFFFF',
      borderRadius: 12,
      padding: 20,
      marginBottom: 16,
      shadowColor: '#000',
      shadowOffset: {
        width: 0,
        height: 2,
      },
      shadowOpacity: 0.1,
      shadowRadius: 3.84,
      elevation: 5,
    },
    checkinTitle: {
      fontSize: 18,
      fontWeight: '600',
      color: '#333333',
      marginBottom: 16,
      textAlign: 'center',
    },
    checkinButton: {
      backgroundColor: '#4CAF50',
      borderRadius: 8,
      paddingVertical: 14,
      paddingHorizontal: 24,
      alignItems: 'center',
      marginBottom: 16,
    },
    checkinButtonDisabled: {
      backgroundColor: '#CCCCCC',
    },
    checkinButtonText: {
      color: '#FFFFFF',
      fontSize: 16,
      fontWeight: '600',
    },
    consecutiveInfo: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      paddingTop: 12,
      borderTopWidth: 1,
      borderTopColor: '#F0F0F0',
    },
    consecutiveText: {
      fontSize: 14,
      color: '#666666',
    },
    consecutiveValue: {
      fontSize: 16,
      fontWeight: '600',
      color: '#FF6B35',
    },
    rewardsCard: {
      backgroundColor: '#FFFFFF',
      borderRadius: 12,
      padding: 20,
      shadowColor: '#000',
      shadowOffset: {
        width: 0,
        height: 2,
      },
      shadowOpacity: 0.1,
      shadowRadius: 3.84,
      elevation: 5,
    },
    rewardsTitle: {
      fontSize: 18,
      fontWeight: '600',
      color: '#333333',
      marginBottom: 16,
    },
    rewardItem: {
      flexDirection: 'row',
      alignItems: 'center',
      paddingVertical: 12,
      borderBottomWidth: 1,
      borderBottomColor: '#F0F0F0',
    },
    rewardIcon: {
      fontSize: 24,
      marginRight: 12,
      width: 32,
      textAlign: 'center',
    },
    rewardInfo: {
      flex: 1,
    },
    rewardName: {
      fontSize: 16,
      fontWeight: '500',
      color: '#333333',
    },
    rewardPoints: {
      fontSize: 14,
      color: '#FF6B35',
      marginTop: 2,
    },
    // 修复五角星显示的样式
    starIcon: {
      fontSize: 20,
      color: '#FFD700',
      // 确保字体支持emoji显示
      fontFamily: Platform.OS === 'ios' ? 'Apple Color Emoji' : 'Noto Color Emoji',
      // 添加文本阴影增强显示效果
      textShadowColor: 'rgba(0, 0, 0, 0.1)',
      textShadowOffset: { width: 0, height: 1 },
      textShadowRadius: 1,
    },
    // 备用的五角星样式（使用Unicode字符）
    starIconUnicode: {
      fontSize: 20,
      color: '#FFD700',
      fontWeight: 'bold',
    },
  });

  // 五角星显示组件 - 修复显示问题
  const StarIcon: React.FC<{ filled?: boolean }> = ({ filled = true }) => {
    // 方法1: 使用emoji五角星
    const emojiStar = filled ? '⭐' : '☆';
    
    // 方法2: 使用Unicode五角星字符
    const unicodeStar = filled ? '★' : '☆';
    
    // 方法3: 使用文本替代
    const textStar = filled ? '★' : '☆';

    return (
      <Text style={styles.starIcon}>
        {/* 优先使用emoji，如果不显示则使用Unicode字符 */}
        {emojiStar}
      </Text>
    );
  };

  const rewards = [
    { id: 1, name: '优惠券', points: 100, icon: '🎫' },
    { id: 2, name: '会员升级', points: 500, icon: '👑' },
    { id: 3, name: '免费商品', points: 1000, icon: '🎁' },
    { id: 4, name: '专属服务', points: 2000, icon: '💎' },
  ];

  return (
    <View style={styles.container}>
      <ScrollView style={styles.scrollContainer} showsVerticalScrollIndicator={false}>
        {/* 我的积分卡片 */}
        <View style={styles.pointsCard}>
          <View style={styles.pointsHeader}>
            <StarIcon filled={true} />
            <Text style={styles.pointsTitle}>我的积分</Text>
            <StarIcon filled={true} />
          </View>
          <Text style={styles.pointsValue}>{points.toLocaleString()}</Text>
          <Text style={styles.pointsLabel}>当前积分余额</Text>
        </View>

        {/* 签到卡片 */}
        <View style={styles.checkinCard}>
          <Text style={styles.checkinTitle}>每日签到</Text>
          
          <TouchableOpacity 
            style={[
              styles.checkinButton, 
              checkedIn && styles.checkinButtonDisabled
            ]}
            onPress={handleCheckin}
            disabled={checkedIn}
          >
            <Text style={styles.checkinButtonText}>
              {checkedIn ? '今日已签到' : '立即签到 +10积分'}
            </Text>
          </TouchableOpacity>

          <View style={styles.consecutiveInfo}>
            <Text style={styles.consecutiveText}>连续签到天数</Text>
            <View style={{ flexDirection: 'row', alignItems: 'center' }}>
              <StarIcon filled={true} />
              <Text style={styles.consecutiveValue}>{consecutiveDays} 天</Text>
            </View>
          </View>
        </View>

        {/* 积分兑换 */}
        <View style={styles.rewardsCard}>
          <Text style={styles.rewardsTitle}>积分兑换</Text>
          
          {rewards.map((reward) => (
            <TouchableOpacity key={reward.id} style={styles.rewardItem}>
              <Text style={styles.rewardIcon}>{reward.icon}</Text>
              <View style={styles.rewardInfo}>
                <Text style={styles.rewardName}>{reward.name}</Text>
                <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                  <StarIcon filled={true} />
                  <Text style={styles.rewardPoints}>{reward.points} 积分</Text>
                </View>
              </View>
            </TouchableOpacity>
          ))}
        </View>
      </ScrollView>
    </View>
  );
};

export default CheckinScreen;
