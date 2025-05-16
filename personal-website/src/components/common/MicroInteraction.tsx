/**
 * MicroInteraction.tsx
 *
 * 描述：微交互组件，为元素添加各种交互效果
 *
 * 功能：
 * - 为元素添加悬停、点击等交互效果
 * - 支持多种预设交互效果
 * - 支持自定义交互效果
 * - 支持链接、按钮等元素
 * - 支持设置交互效果的参数
 *
 * 主要组件/接口：
 * - MicroInteraction：微交互组件
 * - MicroInteractionProps：组件属性接口
 * - InteractionType：交互类型
 *
 * 导出：
 * - MicroInteraction 组件（默认导出）
 */

import React, { ReactNode, ElementType, ComponentProps } from 'react';
import { motion, MotionProps, Variants } from 'framer-motion';
import Link from 'next/link';

// 交互类型
export type InteractionType = 
  | 'scale' 
  | 'lift' 
  | 'pulse' 
  | 'shake' 
  | 'rotate' 
  | 'bounce' 
  | 'glow' 
  | 'ripple'
  | 'custom';

// 组件属性接口
interface MicroInteractionProps<T extends ElementType = 'div'> {
  children: ReactNode;
  as?: T;
  type?: InteractionType;
  href?: string;
  className?: string;
  style?: React.CSSProperties;
  variants?: Variants;
  whileHover?: MotionProps['whileHover'];
  whileTap?: MotionProps['whileTap'];
  onClick?: () => void;
  intensity?: 'light' | 'medium' | 'strong';
  duration?: number;
  disabled?: boolean;
  asChild?: boolean;
  props?: ComponentProps<T>;
}

// 预设交互效果
const presetInteractions = {
  scale: {
    light: { scale: 1.02 },
    medium: { scale: 1.05 },
    strong: { scale: 1.1 }
  },
  lift: {
    light: { y: -2, boxShadow: '0 4px 8px rgba(0, 0, 0, 0.1)' },
    medium: { y: -4, boxShadow: '0 6px 12px rgba(0, 0, 0, 0.15)' },
    strong: { y: -8, boxShadow: '0 8px 16px rgba(0, 0, 0, 0.2)' }
  },
  pulse: {
    light: { scale: [1, 1.02, 1] },
    medium: { scale: [1, 1.05, 1] },
    strong: { scale: [1, 1.1, 1] }
  },
  shake: {
    light: { x: [0, 2, -2, 1, 0] },
    medium: { x: [0, 4, -4, 2, 0] },
    strong: { x: [0, 8, -8, 4, 0] }
  },
  rotate: {
    light: { rotate: 2 },
    medium: { rotate: 5 },
    strong: { rotate: 10 }
  },
  bounce: {
    light: { y: [0, -2, 0] },
    medium: { y: [0, -5, 0] },
    strong: { y: [0, -10, 0] }
  },
  glow: {
    light: { boxShadow: '0 0 5px rgba(var(--primary-rgb), 0.5)' },
    medium: { boxShadow: '0 0 10px rgba(var(--primary-rgb), 0.7)' },
    strong: { boxShadow: '0 0 15px rgba(var(--primary-rgb), 0.9)' }
  }
};

// 点击效果
const tapInteractions = {
  scale: { scale: 0.95 },
  lift: { y: 0, boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)' },
  pulse: { scale: 0.95 },
  shake: { x: 0 },
  rotate: { rotate: 0 },
  bounce: { y: 2 },
  glow: { boxShadow: 'none' },
  ripple: {},
  custom: {}
};

const MicroInteraction = <T extends ElementType = 'div'>({
  children,
  as,
  type = 'scale',
  href,
  className = '',
  style = {},
  variants,
  whileHover,
  whileTap,
  onClick,
  intensity = 'medium',
  duration = 0.3,
  disabled = false,
  asChild = false,
  props = {} as ComponentProps<T>
}: MicroInteractionProps<T>) => {
  // 获取交互效果
  const getHoverEffect = () => {
    if (whileHover) return whileHover;
    if (type === 'custom' && variants) return undefined;
    if (type === 'ripple') return {};
    
    return {
      ...presetInteractions[type][intensity],
      transition: { duration }
    };
  };
  
  // 获取点击效果
  const getTapEffect = () => {
    if (whileTap) return whileTap;
    if (type === 'custom' && variants) return undefined;
    
    return {
      ...tapInteractions[type],
      transition: { duration: duration / 2 }
    };
  };
  
  // 渲染链接
  if (href) {
    return (
      <motion.div
        whileHover={!disabled && getHoverEffect()}
        whileTap={!disabled && getTapEffect()}
        variants={variants}
        style={{
          display: 'inline-block',
          cursor: disabled ? 'default' : 'pointer',
          ...style
        }}
        className={className}
      >
        <Link href={href} {...props}>
          {children}
        </Link>
      </motion.div>
    );
  }
  
  // 渲染自定义元素
  const Component = as || 'div';
  return (
    <motion.div
      as={Component}
      whileHover={!disabled && getHoverEffect()}
      whileTap={!disabled && getTapEffect()}
      variants={variants}
      onClick={!disabled ? onClick : undefined}
      style={{
        cursor: onClick && !disabled ? 'pointer' : style.cursor || 'default',
        ...style
      }}
      className={className}
      {...props}
    >
      {children}
    </motion.div>
  );
};

export default MicroInteraction;
