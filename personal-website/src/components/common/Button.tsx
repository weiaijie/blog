/**
 * Button.tsx
 *
 * 描述：自定义按钮组件，支持多种样式和交互效果
 *
 * 功能：
 * - 支持多种按钮样式（主要、次要、文本、轮廓等）
 * - 支持多种按钮大小
 * - 支持图标按钮
 * - 支持加载状态
 * - 支持禁用状态
 * - 支持自定义交互效果
 *
 * 主要组件/接口：
 * - Button：按钮组件
 * - ButtonProps：按钮属性接口
 *
 * 导出：
 * - Button 组件（默认导出）
 */

import React, { ReactNode } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import MicroInteraction, { InteractionType } from './MicroInteraction';
import styles from '@/styles/Button.module.css';

export type ButtonVariant = 'primary' | 'secondary' | 'text' | 'outline' | 'ghost';
export type ButtonSize = 'small' | 'medium' | 'large';

interface ButtonProps {
  children: ReactNode;
  variant?: ButtonVariant;
  size?: ButtonSize;
  href?: string;
  onClick?: () => void;
  className?: string;
  disabled?: boolean;
  loading?: boolean;
  fullWidth?: boolean;
  icon?: ReactNode;
  iconPosition?: 'left' | 'right';
  interactionType?: InteractionType;
  interactionIntensity?: 'light' | 'medium' | 'strong';
  ariaLabel?: string;
}

const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'medium',
  href,
  onClick,
  className = '',
  disabled = false,
  loading = false,
  fullWidth = false,
  icon,
  iconPosition = 'left',
  interactionType = 'scale',
  interactionIntensity = 'medium',
  ariaLabel
}) => {
  // 构建按钮类名
  const buttonClasses = [
    styles.button,
    styles[`button-${variant}`],
    styles[`button-${size}`],
    fullWidth ? styles.fullWidth : '',
    loading ? styles.loading : '',
    className
  ].filter(Boolean).join(' ');
  
  // 加载指示器
  const loadingIndicator = (
    <span className={styles.loadingIndicator}>
      <span className={styles.loadingDot}></span>
      <span className={styles.loadingDot}></span>
      <span className={styles.loadingDot}></span>
    </span>
  );
  
  // 按钮内容
  const buttonContent = (
    <>
      {loading ? loadingIndicator : (
        <>
          {icon && iconPosition === 'left' && (
            <span className={styles.iconLeft}>{icon}</span>
          )}
          <span className={styles.buttonText}>{children}</span>
          {icon && iconPosition === 'right' && (
            <span className={styles.iconRight}>{icon}</span>
          )}
        </>
      )}
    </>
  );
  
  // 如果是链接按钮
  if (href && !disabled) {
    return (
      <MicroInteraction
        type={interactionType}
        intensity={interactionIntensity}
        href={href}
        className={buttonClasses}
        disabled={disabled || loading}
      >
        {buttonContent}
      </MicroInteraction>
    );
  }
  
  // 普通按钮
  return (
    <MicroInteraction
      as="button"
      type={interactionType}
      intensity={interactionIntensity}
      className={buttonClasses}
      onClick={onClick}
      disabled={disabled || loading}
      props={{
        type: 'button',
        disabled: disabled || loading,
        'aria-label': ariaLabel,
        'aria-disabled': disabled || loading
      }}
    >
      {buttonContent}
    </MicroInteraction>
  );
};

export default Button;
