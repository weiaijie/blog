/**
 * useReducedMotion.ts
 *
 * 描述：检测用户动画偏好的自定义Hook
 *
 * 功能：
 * - 检测用户的prefers-reduced-motion设置
 * - 为不喜欢动画的用户提供静态体验
 * - 支持服务端渲染
 *
 * 主要功能：
 * - useReducedMotion：检测动画偏好的Hook
 * - getReducedMotionVariants：获取适配的动画变体
 *
 * 导出：
 * - useReducedMotion Hook（默认导出）
 * - getReducedMotionVariants 工具函数
 */

import { useState, useEffect } from 'react';

/**
 * 检测用户是否偏好减少动画
 * @returns boolean - true表示用户偏好减少动画
 */
export const useReducedMotion = (): boolean => {
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);

  useEffect(() => {
    // 检查是否在客户端环境
    if (typeof window === 'undefined') {
      return;
    }

    // 检查浏览器是否支持matchMedia
    if (!window.matchMedia) {
      return;
    }

    // 创建媒体查询
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    
    // 设置初始值
    setPrefersReducedMotion(mediaQuery.matches);

    // 监听变化
    const handleChange = (event: MediaQueryListEvent) => {
      setPrefersReducedMotion(event.matches);
    };

    // 添加监听器
    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', handleChange);
    } else {
      // 兼容旧版浏览器
      mediaQuery.addListener(handleChange);
    }

    // 清理函数
    return () => {
      if (mediaQuery.removeEventListener) {
        mediaQuery.removeEventListener('change', handleChange);
      } else {
        // 兼容旧版浏览器
        mediaQuery.removeListener(handleChange);
      }
    };
  }, []);

  return prefersReducedMotion;
};

/**
 * 动画变体接口
 */
interface AnimationVariants {
  [key: string]: any;
  hidden?: any;
  visible?: any;
  initial?: any;
  animate?: any;
  exit?: any;
  transition?: any;
  whileHover?: any;
  whileTap?: any;
  whileInView?: any;
}

/**
 * 根据用户偏好获取适配的动画变体
 * @param variants - 原始动画变体
 * @param prefersReducedMotion - 是否偏好减少动画
 * @returns 适配后的动画变体
 */
export const getReducedMotionVariants = (
  variants: AnimationVariants,
  prefersReducedMotion: boolean
): AnimationVariants => {
  if (!prefersReducedMotion) {
    return variants;
  }

  // 为偏好减少动画的用户提供静态版本
  const reducedVariants: AnimationVariants = {};

  // 保留位置和透明度的最终状态，但移除动画
  if (variants.hidden && variants.visible) {
    reducedVariants.hidden = {
      opacity: variants.visible.opacity || 1,
      x: variants.visible.x || 0,
      y: variants.visible.y || 0,
      scale: variants.visible.scale || 1,
      rotate: variants.visible.rotate || 0,
    };
    reducedVariants.visible = {
      opacity: variants.visible.opacity || 1,
      x: variants.visible.x || 0,
      y: variants.visible.y || 0,
      scale: variants.visible.scale || 1,
      rotate: variants.visible.rotate || 0,
    };
  }

  // 移除过渡动画
  if (variants.transition) {
    reducedVariants.transition = { duration: 0 };
  }

  // 保留悬停效果但减少动画
  if (variants.whileHover) {
    reducedVariants.whileHover = {
      ...variants.whileHover,
      transition: { duration: 0.1 }
    };
  }

  // 保留点击效果但减少动画
  if (variants.whileTap) {
    reducedVariants.whileTap = {
      ...variants.whileTap,
      transition: { duration: 0.05 }
    };
  }

  // 移除滚动触发动画
  if (variants.whileInView) {
    reducedVariants.whileInView = {
      opacity: 1,
      x: 0,
      y: 0,
      scale: 1,
      rotate: 0,
    };
  }

  return reducedVariants;
};

/**
 * 获取适配的过渡配置
 * @param transition - 原始过渡配置
 * @param prefersReducedMotion - 是否偏好减少动画
 * @returns 适配后的过渡配置
 */
export const getReducedMotionTransition = (
  transition: any,
  prefersReducedMotion: boolean
): any => {
  if (!prefersReducedMotion) {
    return transition;
  }

  // 为偏好减少动画的用户提供快速过渡
  return {
    duration: 0.1,
    ease: "linear"
  };
};

/**
 * 获取适配的延迟配置
 * @param delay - 原始延迟时间
 * @param prefersReducedMotion - 是否偏好减少动画
 * @returns 适配后的延迟时间
 */
export const getReducedMotionDelay = (
  delay: number,
  prefersReducedMotion: boolean
): number => {
  if (!prefersReducedMotion) {
    return delay;
  }

  // 为偏好减少动画的用户移除延迟
  return 0;
};

export default useReducedMotion;
