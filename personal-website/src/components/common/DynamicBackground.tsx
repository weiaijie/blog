/**
 * DynamicBackground.tsx
 *
 * 描述：动态背景组件，为页面或区域添加各种动态背景效果
 *
 * 功能：
 * - 提供多种动态背景效果（渐变、粒子、波浪等）
 * - 支持自定义背景颜色和动画参数
 * - 支持响应鼠标移动的交互效果
 * - 支持设置背景层级和透明度
 *
 * 主要组件/接口：
 * - DynamicBackground：动态背景组件
 * - DynamicBackgroundProps：组件属性接口
 * - BackgroundType：背景类型
 *
 * 导出：
 * - DynamicBackground 组件（默认导出）
 */

import React, { useRef, useEffect, useState } from 'react';
import { motion, useMotionValue, useTransform, useSpring } from 'framer-motion';
import styles from '@/styles/DynamicBackground.module.css';

// 背景类型
export type BackgroundType = 
  | 'gradient' 
  | 'particles' 
  | 'waves' 
  | 'grid' 
  | 'noise'
  | 'custom';

interface DynamicBackgroundProps {
  type?: BackgroundType;
  className?: string;
  style?: React.CSSProperties;
  colors?: string[];
  interactive?: boolean;
  speed?: 'slow' | 'medium' | 'fast';
  opacity?: number;
  zIndex?: number;
  particleCount?: number;
  children?: React.ReactNode;
}

const DynamicBackground: React.FC<DynamicBackgroundProps> = ({
  type = 'gradient',
  className = '',
  style = {},
  colors = ['rgba(var(--primary-rgb), 0.1)', 'rgba(var(--secondary-rgb), 0.1)', 'rgba(var(--accent-rgb), 0.1)'],
  interactive = true,
  speed = 'medium',
  opacity = 0.8,
  zIndex = -1,
  particleCount = 50,
  children
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });
  
  // 鼠标位置状态
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);
  
  // 动画速度映射
  const speedMap = {
    slow: 30,
    medium: 15,
    fast: 8
  };
  
  // 背景位置变换
  const x = useTransform(mouseX, [-500, 500], [10, -10]);
  const y = useTransform(mouseY, [-500, 500], [10, -10]);
  
  // 使用spring添加平滑效果
  const springX = useSpring(x, { stiffness: 100, damping: 30 });
  const springY = useSpring(y, { stiffness: 100, damping: 30 });
  
  // 处理鼠标移动
  const handleMouseMove = (e: React.MouseEvent) => {
    if (!interactive || !containerRef.current) return;
    
    const rect = containerRef.current.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    
    mouseX.set(e.clientX - centerX);
    mouseY.set(e.clientY - centerY);
  };
  
  // 鼠标离开时重置
  const handleMouseLeave = () => {
    mouseX.set(0);
    mouseY.set(0);
  };
  
  // 更新容器尺寸
  useEffect(() => {
    if (!containerRef.current) return;
    
    const updateDimensions = () => {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.offsetWidth,
          height: containerRef.current.offsetHeight
        });
      }
    };
    
    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    
    return () => {
      window.removeEventListener('resize', updateDimensions);
    };
  }, []);
  
  // 生成粒子
  const generateParticles = () => {
    return Array.from({ length: particleCount }).map((_, index) => {
      const size = Math.random() * 6 + 2;
      return (
        <motion.div
          key={index}
          className={styles.particle}
          style={{
            width: size,
            height: size,
            left: `${Math.random() * 100}%`,
            top: `${Math.random() * 100}%`,
            backgroundColor: colors[Math.floor(Math.random() * colors.length)],
            opacity: Math.random() * 0.5 + 0.3
          }}
          animate={{
            y: [0, Math.random() * 30 - 15, 0],
            x: [0, Math.random() * 30 - 15, 0],
            scale: [1, Math.random() * 0.5 + 0.8, 1]
          }}
          transition={{
            duration: Math.random() * 5 + speedMap[speed],
            repeat: Infinity,
            repeatType: 'reverse',
            ease: 'easeInOut'
          }}
        />
      );
    });
  };
  
  // 渲染背景内容
  const renderBackgroundContent = () => {
    switch (type) {
      case 'particles':
        return generateParticles();
      case 'waves':
        return (
          <div className={styles.waves}>
            {Array.from({ length: 3 }).map((_, index) => (
              <motion.div
                key={index}
                className={styles.wave}
                style={{
                  backgroundImage: `linear-gradient(90deg, ${colors.join(', ')})`,
                  opacity: 0.1 + index * 0.1,
                  animationDuration: `${speedMap[speed] + index * 2}s`
                }}
              />
            ))}
          </div>
        );
      case 'grid':
        return (
          <div 
            className={styles.grid}
            style={{
              backgroundSize: `${20 + speedMap[speed]}px ${20 + speedMap[speed]}px`,
              backgroundImage: `linear-gradient(to right, ${colors[0]} 1px, transparent 1px), 
                               linear-gradient(to bottom, ${colors[0]} 1px, transparent 1px)`
            }}
          />
        );
      case 'noise':
        return (
          <div 
            className={styles.noise}
            style={{
              animationDuration: `${speedMap[speed] / 2}s`
            }}
          />
        );
      case 'gradient':
      default:
        return (
          <motion.div
            className={styles.gradient}
            style={{
              backgroundImage: `linear-gradient(135deg, ${colors.join(', ')})`,
              backgroundSize: '400% 400%',
              x: interactive ? springX : 0,
              y: interactive ? springY : 0
            }}
            animate={{
              backgroundPosition: ['0% 0%', '100% 100%', '0% 0%']
            }}
            transition={{
              duration: speedMap[speed] * 2,
              repeat: Infinity,
              repeatType: 'reverse',
              ease: 'easeInOut'
            }}
          />
        );
    }
  };
  
  return (
    <motion.div
      ref={containerRef}
      className={`${styles.dynamicBackground} ${className}`}
      style={{
        ...style,
        opacity,
        zIndex
      }}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
    >
      {renderBackgroundContent()}
      {children}
    </motion.div>
  );
};

export default DynamicBackground;
