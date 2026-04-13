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

import { useState, useEffect } from 'react';
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
  const [charIndex, setCharIndex] = useState(0);

  // 打字效果
  useEffect(() => {
    if (!texts || texts.length === 0) return;

    const currentText = texts[textIndex];
    const timer = window.setTimeout(() => {
      if (isTyping) {
        if (charIndex < currentText.length) {
          const nextIndex = charIndex + 1;
          setCharIndex(nextIndex);
          setDisplayText(currentText.slice(0, nextIndex));
          return;
        }

        setIsTyping(false);
        return;
      }

      if (charIndex > 0) {
        const nextIndex = charIndex - 1;
        setCharIndex(nextIndex);
        setDisplayText(currentText.slice(0, nextIndex));
        return;
      }

      if (loop || textIndex < texts.length - 1) {
        setTextIndex((prevIndex) => (prevIndex + 1) % texts.length);
      } else {
        setDisplayText(currentText);
        setCharIndex(currentText.length);
      }
      setIsTyping(true);
    }, isTyping
      ? (charIndex < currentText.length ? typingSpeed : delayAfterType)
      : (charIndex > 0 ? deletingSpeed : delayAfterDelete));

    return () => window.clearTimeout(timer);
  }, [charIndex, isTyping, textIndex, texts, typingSpeed, deletingSpeed, delayAfterType, delayAfterDelete, loop]);

  useEffect(() => {
    setDisplayText('');
    setCharIndex(0);
    setIsTyping(true);
    setTextIndex(0);
  }, [texts]);

  return (
    <span className={`${styles.typewriter} ${className}`}>
      {displayText}
      <span className={styles.cursor}></span>
    </span>
  );
};

export default Typewriter;
