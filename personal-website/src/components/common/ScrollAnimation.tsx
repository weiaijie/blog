/**
 * ScrollAnimation.tsx
 *
 * 描述：增强的滚动动画组件，用于在元素进入视口时触发各种动画效果
 *
 * 功能：
 * - 监测元素是否进入视口
 * - 当元素进入视口时触发动画
 * - 支持多种预设动画效果（淡入、上移、缩放等）
 * - 支持自定义动画变体
 * - 支持设置动画延迟
 * - 支持设置触发阈值
 * - 支持设置动画是否只触发一次
 * - 支持设置动画持续时间
 * - 支持设置动画缓动函数
 *
 * 主要组件/接口：
 * - ScrollAnimation：滚动动画组件
 * - ScrollAnimationProps：组件属性接口
 * - AnimationPreset：预设动画类型
 * - defaultVariants：默认动画变体
 *
 * 导出：
 * - ScrollAnimation 组件（默认导出）
 */

import React, { ReactNode, useEffect, useRef } from 'react';
import { motion, useAnimation, Variants, MotionStyle } from 'framer-motion';
import { useInView } from 'framer-motion';

// 预设动画类型
export type AnimationPreset =
  | 'fadeIn'
  | 'fadeInUp'
  | 'fadeInDown'
  | 'fadeInLeft'
  | 'fadeInRight'
  | 'zoomIn'
  | 'zoomInRotate'
  | 'slideUp'
  | 'slideDown'
  | 'slideLeft'
  | 'slideRight'
  | 'flipX'
  | 'flipY'
  | 'bounce'
  | 'pulse'
  | 'custom';

interface ScrollAnimationProps {
  children: ReactNode;
  preset?: AnimationPreset;
  variants?: Variants;
  className?: string;
  style?: MotionStyle;
  delay?: number;
  duration?: number;
  threshold?: number;
  once?: boolean;
  staggerChildren?: number;
  staggerDirection?: 'forward' | 'reverse';
  ease?: string | number[];
  distance?: number;
}

// 预设动画变体
const presetVariants = {
  fadeIn: {
    hidden: { opacity: 0 },
    visible: { opacity: 1 }
  },
  fadeInUp: {
    hidden: { opacity: 0, y: 50 },
    visible: { opacity: 1, y: 0 }
  },
  fadeInDown: {
    hidden: { opacity: 0, y: -50 },
    visible: { opacity: 1, y: 0 }
  },
  fadeInLeft: {
    hidden: { opacity: 0, x: -50 },
    visible: { opacity: 1, x: 0 }
  },
  fadeInRight: {
    hidden: { opacity: 0, x: 50 },
    visible: { opacity: 1, x: 0 }
  },
  zoomIn: {
    hidden: { opacity: 0, scale: 0.8 },
    visible: { opacity: 1, scale: 1 }
  },
  zoomInRotate: {
    hidden: { opacity: 0, scale: 0.8, rotate: -10 },
    visible: { opacity: 1, scale: 1, rotate: 0 }
  },
  slideUp: {
    hidden: { y: 100 },
    visible: { y: 0 }
  },
  slideDown: {
    hidden: { y: -100 },
    visible: { y: 0 }
  },
  slideLeft: {
    hidden: { x: -100 },
    visible: { x: 0 }
  },
  slideRight: {
    hidden: { x: 100 },
    visible: { x: 0 }
  },
  flipX: {
    hidden: { opacity: 0, rotateX: 90 },
    visible: { opacity: 1, rotateX: 0 }
  },
  flipY: {
    hidden: { opacity: 0, rotateY: 90 },
    visible: { opacity: 1, rotateY: 0 }
  },
  bounce: {
    hidden: { opacity: 0, y: 50 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        type: 'spring',
        stiffness: 300,
        damping: 10
      }
    }
  },
  pulse: {
    hidden: { opacity: 0, scale: 0.8 },
    visible: {
      opacity: 1,
      scale: [0.8, 1.1, 1],
      transition: {
        times: [0, 0.7, 1]
      }
    }
  }
};

// 默认动画变体
const defaultVariants: Variants = {
  hidden: {
    opacity: 0,
    y: 30
  },
  visible: {
    opacity: 1,
    y: 0
  }
};

const ScrollAnimation: React.FC<ScrollAnimationProps> = ({
  children,
  preset = 'fadeInUp',
  variants,
  className = '',
  style = {},
  delay = 0,
  duration = 0.6,
  threshold = 0.1,
  once = true,
  staggerChildren = 0,
  staggerDirection = 'forward',
  ease = [0.16, 1, 0.3, 1],
  distance = 50
}) => {
  const ref = useRef(null);
  const isInView = useInView(ref, { once, amount: threshold });
  const controls = useAnimation();

  // 根据预设和自定义参数生成最终的动画变体
  const getVariants = (): Variants => {
    if (variants) return variants;

    if (preset === 'custom') return defaultVariants;

    // 克隆预设变体以避免修改原始对象
    const selectedPreset = JSON.parse(JSON.stringify(presetVariants[preset] || defaultVariants));

    // 自定义距离
    if (preset.includes('Up') || preset.includes('Down')) {
      selectedPreset.hidden.y = preset.includes('Up') ? distance : -distance;
    } else if (preset.includes('Left') || preset.includes('Right')) {
      selectedPreset.hidden.x = preset.includes('Left') ? -distance : distance;
    }

    // 添加过渡属性
    selectedPreset.visible.transition = {
      duration,
      ease,
      delay,
      ...(staggerChildren > 0 && {
        staggerChildren,
        staggerDirection,
        when: 'beforeChildren'
      })
    };

    return selectedPreset;
  };

  useEffect(() => {
    if (isInView) {
      controls.start('visible');
    } else if (!once) {
      controls.start('hidden');
    }
  }, [isInView, controls, once]);

  return (
    <motion.div
      ref={ref}
      initial="hidden"
      animate={controls}
      variants={getVariants()}
      className={className}
      style={{
        willChange: 'opacity, transform',
        ...style
      }}
    >
      {children}
    </motion.div>
  );
};

export default ScrollAnimation;
