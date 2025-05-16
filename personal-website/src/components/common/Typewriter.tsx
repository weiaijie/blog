/**
 * Typewriter.tsx
 *
 * 描述：打字机效果组件，用于创建文字逐字显示和删除的动画效果
 *
 * 功能：
 * - 实现文字逐字显示的打字效果
 * - 实现文字逐字删除的效果
 * - 支持多段文本循环显示
 * - 可自定义打字速度、删除速度和延迟时间
 * - 支持循环播放或单次播放
 *
 * 主要组件/接口：
 * - Typewriter：打字机效果组件
 * - TypewriterProps：组件属性接口
 *
 * 导出：
 * - Typewriter 组件（默认导出）
 */

import { useState, useEffect, useRef } from 'react';
import styles from '@/styles/Typewriter.module.css';

interface TypewriterProps {
  texts: string[];
  typingSpeed?: number;
  deletingSpeed?: number;
  delayAfterType?: number;
  delayAfterDelete?: number;
  loop?: boolean;
  className?: string;
}

const Typewriter = ({
  texts,
  typingSpeed = 100,
  deletingSpeed = 50,
  delayAfterType = 2000,
  delayAfterDelete = 500,
  loop = true,
  className = '',
}: TypewriterProps) => {
  const [displayText, setDisplayText] = useState('');
  const [isTyping, setIsTyping] = useState(true);
  const [textIndex, setTextIndex] = useState(0);
  const currentTextRef = useRef('');
  const currentIndexRef = useRef(0);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // 清除定时器
  const clearTimer = () => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  };

  // 打字效果
  useEffect(() => {
    // 确保有文本可以显示
    if (!texts || texts.length === 0) return;

    const currentText = texts[textIndex];
    currentTextRef.current = currentText;

    // 打字过程
    if (isTyping) {
      if (currentIndexRef.current < currentText.length) {
        // 继续打字
        clearTimer();
        timerRef.current = setTimeout(() => {
          currentIndexRef.current += 1;
          setDisplayText(currentText.substring(0, currentIndexRef.current));
        }, typingSpeed);
      } else {
        // 打字完成，等待一段时间后开始删除
        clearTimer();
        timerRef.current = setTimeout(() => {
          setIsTyping(false);
        }, delayAfterType);
      }
    } else {
      // 删除过程
      if (currentIndexRef.current > 0) {
        // 继续删除
        clearTimer();
        timerRef.current = setTimeout(() => {
          currentIndexRef.current -= 1;
          setDisplayText(currentText.substring(0, currentIndexRef.current));
        }, deletingSpeed);
      } else {
        // 删除完成，准备打字下一个文本
        clearTimer();
        timerRef.current = setTimeout(() => {
          setIsTyping(true);
          setTextIndex((prevIndex) => (loop || prevIndex < texts.length - 1 ? (prevIndex + 1) % texts.length : prevIndex));
        }, delayAfterDelete);
      }
    }

    // 组件卸载时清除定时器
    return () => clearTimer();
  }, [displayText, isTyping, textIndex, texts, typingSpeed, deletingSpeed, delayAfterType, delayAfterDelete, loop]);

  return (
    <span className={`${styles.typewriter} ${className}`}>
      {displayText}
      <span className={styles.cursor}></span>
    </span>
  );
};

export default Typewriter;
