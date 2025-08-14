/**
 * ScrollAnimation.tsx
 *
 * 描述：滚动动画组件，用于在元素进入视口时触发动画效果
 *
 * 功能：
 * - 监测元素是否进入视口
 * - 当元素进入视口时触发动画
 * - 支持自定义动画变体
 * - 支持设置动画延迟
 * - 支持设置触发阈值
 * - 支持设置动画是否只触发一次
 *
 * 主要组件/接口：
 * - ScrollAnimation：滚动动画组件
 * - ScrollAnimationProps：组件属性接口
 * - defaultVariants：默认动画变体
 *
 * 导出：
 * - ScrollAnimation 组件（默认导出）
 */

import React, { ReactNode, useEffect, useRef } from 'react';
import { motion, useAnimation, Variants } from 'framer-motion';
import { useInView } from 'framer-motion';

interface ScrollAnimationProps {
  children: ReactNode;
  variants?: Variants;
  className?: string;
  delay?: number;
  threshold?: number;
  once?: boolean;
}

const defaultVariants: Variants = {
  hidden: {
    opacity: 0,
    y: 30
  },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.6,
      ease: [0.16, 1, 0.3, 1]
    }
  }
};

const ScrollAnimation: React.FC<ScrollAnimationProps> = ({
  children,
  variants = defaultVariants,
  className = '',
  delay = 0,
  threshold = 0.1,
  once = true
}) => {
  const ref = useRef(null);
  const isInView = useInView(ref, { once, amount: threshold });
  const controls = useAnimation();

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
      variants={variants}
      className={className}
      transition={{ delay }}
    >
      {children}
    </motion.div>
  );
};

export default ScrollAnimation;
