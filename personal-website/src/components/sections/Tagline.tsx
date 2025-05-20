/**
 * Tagline.tsx
 *
 * 描述：网站标语组件，展示在首页顶部的主要宣传语和行动按钮
 *
 * 功能：
 * - 展示网站的主要标语和副标语
 * - 使用打字机效果展示多个标语文本
 * - 提供"查看作品"和"联系我"的行动按钮
 * - 支持平滑的显示/隐藏动画效果
 * - 响应滚动事件，在向下滚动时隐藏
 * - 支持3D变换效果和鼠标交互
 * - 包含动态背景和浮动元素
 *
 * 主要组件/接口：
 * - Tagline：标语组件
 * - TaglineProps：组件属性接口
 *
 * 导出：
 * - Tagline 组件（默认导出）
 */

import React, { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { motion, AnimatePresence, useMotionValue, useTransform, useSpring } from 'framer-motion';
import styles from '@/styles/Tagline.module.css';
import Typewriter from '@/components/common/Typewriter';

interface TaglineProps {
  visible: boolean; // 控制是否显示
}

const Tagline: React.FC<TaglineProps> = ({ visible }) => {
  const prevVisibleRef = useRef(visible);
  const containerRef = useRef<HTMLDivElement>(null);

  // 鼠标位置状态
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);

  // 3D变换效果的值
  const rotateX = useTransform(mouseY, [-300, 300], [5, -5]);
  const rotateY = useTransform(mouseX, [-300, 300], [-5, 5]);

  // 使用spring添加平滑效果
  const springRotateX = useSpring(rotateX, { stiffness: 100, damping: 30 });
  const springRotateY = useSpring(rotateY, { stiffness: 100, damping: 30 });

  // 浮动元素位置
  const [floatingElements, setFloatingElements] = useState([
    { id: 1, x: -20, y: 30, size: 40, delay: 0 },
    { id: 2, x: 50, y: -40, size: 30, delay: 0.5 },
    { id: 3, x: 80, y: 60, size: 25, delay: 1 },
    { id: 4, x: -60, y: -20, size: 35, delay: 1.5 },
  ]);

  // 处理鼠标移动
  const handleMouseMove = (e: React.MouseEvent) => {
    if (!containerRef.current) return;

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

  // 定义动画变体 - 进一步优化过渡效果，避免影响滚动和页面跳动
  const containerVariants = {
    hidden: {
      opacity: 0,
      y: 0,
      transition: {
        duration: 0.4,
        ease: "easeInOut"
      }
    },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.4,
        ease: "easeInOut",
        when: "beforeChildren",
        staggerChildren: 0.05
      }
    },
    exit: {
      opacity: 0,
      y: 0,
      transition: {
        duration: 0.3,
        ease: "easeInOut"
      }
    }
  };

  // 更新visible状态引用
  useEffect(() => {
    prevVisibleRef.current = visible;
  }, [visible]);

  const childVariants = {
    hidden: { opacity: 0, y: 10 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.3,
        ease: "easeOut"
      }
    }
  };

  // 浮动元素动画变体
  const floatingVariants = {
    animate: (i: number) => ({
      y: [0, -15, 0],
      x: [0, 5, 0],
      transition: {
        y: {
          repeat: Infinity,
          duration: 3,
          ease: "easeInOut",
          delay: i * 0.2
        },
        x: {
          repeat: Infinity,
          duration: 4,
          ease: "easeInOut",
          delay: i * 0.3
        }
      }
    })
  };

  // 代码片段元素 - 使用简单的打字机效果，展示多种编程语言
  const CodeSnippet = () => {
    // 定义多个代码示例
    const codeExamples = [
      // JavaScript/React 示例
      {
        language: 'JavaScript',
        lines: [
          { text: 'const createExperience = () => {', indent: 0 },
          { text: 'return "Amazing";', indent: 2 },
          { text: '}', indent: 0 }
        ]
      },
      // Python 示例
      {
        language: 'Python',
        lines: [
          { text: 'def create_experience():', indent: 0 },
          { text: 'return "Amazing"', indent: 4 }
        ]
      },
      // TypeScript 示例
      {
        language: 'TypeScript',
        lines: [
          { text: 'function processData<T>(data: T): T {', indent: 0 },
          { text: 'console.log("Processing...");', indent: 2 },
          { text: 'return data;', indent: 2 },
          { text: '}', indent: 0 }
        ]
      },
      // PHP 示例
      {
        language: 'PHP',
        lines: [
          { text: 'function createExperience() {', indent: 0 },
          { text: '$result = "Amazing";', indent: 2 },
          { text: 'return $result;', indent: 2 },
          { text: '}', indent: 0 }
        ]
      },
      // CSS 示例
      {
        language: 'CSS',
        lines: [
          { text: '.container {', indent: 0 },
          { text: 'display: flex;', indent: 2 },
          { text: 'justify-content: center;', indent: 2 },
          { text: 'align-items: center;', indent: 2 },
          { text: '}', indent: 0 }
        ]
      }
    ];

    // 当前显示的代码示例索引
    const [currentExampleIndex, setCurrentExampleIndex] = useState(0);

    // 获取当前代码示例
    const currentExample = codeExamples[currentExampleIndex];
    const codeLines = currentExample.lines;

    // 跟踪当前显示的行数
    const [currentLineIndex, setCurrentLineIndex] = useState(0);
    const [currentCharIndex, setCurrentCharIndex] = useState(0);
    const [showCursor, setShowCursor] = useState(true);
    const [typingSpeed, setTypingSpeed] = useState(50); // 打字速度
    const timerRef = useRef<NodeJS.Timeout | null>(null);

    // 清除定时器
    const clearTimer = () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }
    };

    // 闪烁光标效果
    useEffect(() => {
      const cursorInterval = setInterval(() => {
        setShowCursor(prev => !prev);
      }, 500);

      return () => clearInterval(cursorInterval);
    }, []);

    // 切换代码示例
    useEffect(() => {
      // 当完成一个示例后，等待一段时间再切换到下一个示例
      if (currentLineIndex >= codeLines.length) {
        clearTimer();
        timerRef.current = setTimeout(() => {
          // 切换到下一个代码示例
          setCurrentExampleIndex((prevIndex) => (prevIndex + 1) % codeExamples.length);
          // 重置行和字符索引
          setCurrentLineIndex(0);
          setCurrentCharIndex(0);
        }, 3000);
        return;
      }

      // 获取当前行
      const currentLine = codeLines[currentLineIndex];
      const lineText = currentLine.text;

      // 如果已经完成当前行
      if (currentCharIndex >= lineText.length) {
        clearTimer();
        timerRef.current = setTimeout(() => {
          setCurrentLineIndex(prev => prev + 1);
          setCurrentCharIndex(0);
        }, 500);
        return;
      }

      // 继续打字当前行
      clearTimer();
      timerRef.current = setTimeout(() => {
        setCurrentCharIndex(prev => prev + 1);
      }, typingSpeed);

      return () => clearTimer();
    }, [currentLineIndex, currentCharIndex, codeLines.length, codeExamples.length]);

    // 组件卸载时清除定时器
    useEffect(() => {
      return () => clearTimer();
    }, []);

    // 监听窗口大小变化，调整打字速度
    useEffect(() => {
      const handleResize = () => {
        // 在移动设备上使用更快的打字速度
        setTypingSpeed(window.innerWidth <= 768 ? 30 : 50);
      };

      // 初始化
      handleResize();

      // 添加事件监听器
      window.addEventListener('resize', handleResize);

      // 清理
      return () => window.removeEventListener('resize', handleResize);
    }, []);

    // 渲染代码行
    const renderCodeLines = () => {
      return codeLines.map((line, lineIndex) => {
        // 如果还没到这一行，不显示
        if (lineIndex > currentLineIndex) {
          return null;
        }

        // 当前正在打字的行
        if (lineIndex === currentLineIndex) {
          const displayedText = line.text.substring(0, currentCharIndex);
          const indentSpaces = '\u00A0\u00A0'.repeat(line.indent);

          // 如果已经完成了整行，使用高亮版本
          if (currentCharIndex >= line.text.length) {
            return (
              <div key={lineIndex} className={styles.codeLine} style={{ textAlign: 'left' }}>
                {line.indent > 0 && <span>{indentSpaces}</span>}
                {getHighlightedText(line.text)}
                {showCursor && <span className={styles.cursor}></span>}
              </div>
            );
          }

          // 为当前正在打字的行添加语法高亮
          let highlightedText;
          const typedLength = displayedText.length;
          const language = currentExample.language;

          // 如果打字长度很短，直接显示文本
          if (typedLength <= 2) {
            highlightedText = <>{displayedText}</>;
          }
          // JavaScript 高亮
          else if (language === 'JavaScript') {
            if (line.text.includes('const')) {
              if (typedLength >= 5) { // 'const'
                highlightedText = (
                  <>
                    <span className={styles.keyword}>const</span>
                    {typedLength > 5 && ' '}
                    {typedLength > 6 && (
                      <span className={styles.variable}>
                        {displayedText.substring(6, Math.min(typedLength, 22))}
                      </span>
                    )}
                    {typedLength > 22 && ' '}
                    {typedLength > 23 && <span className={styles.operator}>=</span>}
                    {typedLength > 24 && ' '}
                    {typedLength > 25 && <span className={styles.punctuation}>()</span>}
                    {typedLength > 27 && ' '}
                    {typedLength > 28 && <span className={styles.operator}>=&gt;</span>}
                    {typedLength > 30 && ' '}
                    {typedLength > 31 && <span className={styles.punctuation}>{'{'}</span>}
                  </>
                );
              } else {
                highlightedText = <>{displayedText}</>;
              }
            } else if (line.text.includes('return')) {
              if (typedLength >= 6) { // 'return'
                highlightedText = (
                  <>
                    <span className={styles.keyword}>return</span>
                    {typedLength > 6 && ' '}
                    {typedLength > 7 && (
                      <span className={styles.string}>
                        {displayedText.substring(7, Math.min(typedLength, 16))}
                      </span>
                    )}
                    {typedLength > 16 && <span className={styles.punctuation}>;</span>}
                  </>
                );
              } else {
                highlightedText = <>{displayedText}</>;
              }
            } else if (line.text === '}') {
              highlightedText = <span className={styles.punctuation}>{'}'}</span>;
            } else {
              highlightedText = <>{displayedText}</>;
            }
          }
          // Python 高亮
          else if (language === 'Python') {
            if (line.text.includes('def')) {
              if (typedLength >= 3) { // 'def'
                highlightedText = (
                  <>
                    <span className={styles.keyword}>def</span>
                    {typedLength > 3 && ' '}
                    {typedLength > 4 && (
                      <span className={styles.variable}>
                        {displayedText.substring(4, Math.min(typedLength, 20))}
                      </span>
                    )}
                    {typedLength > 20 && <span className={styles.punctuation}>()</span>}
                    {typedLength > 22 && <span className={styles.punctuation}>:</span>}
                  </>
                );
              } else {
                highlightedText = <>{displayedText}</>;
              }
            } else if (line.text.includes('return')) {
              if (typedLength >= 6) { // 'return'
                highlightedText = (
                  <>
                    <span className={styles.keyword}>return</span>
                    {typedLength > 6 && ' '}
                    {typedLength > 7 && (
                      <span className={styles.string}>
                        {displayedText.substring(7, Math.min(typedLength, 16))}
                      </span>
                    )}
                  </>
                );
              } else {
                highlightedText = <>{displayedText}</>;
              }
            } else {
              highlightedText = <>{displayedText}</>;
            }
          }
          // TypeScript 高亮
          else if (language === 'TypeScript') {
            if (line.text.includes('function')) {
              if (typedLength >= 8) { // 'function'
                highlightedText = (
                  <>
                    <span className={styles.keyword}>function</span>
                    {typedLength > 8 && ' '}
                    {typedLength > 9 && (
                      <span className={styles.variable}>
                        {displayedText.substring(9, Math.min(typedLength, 20))}
                      </span>
                    )}
                    {/* 其余部分省略，根据需要添加 */}
                  </>
                );
              } else {
                highlightedText = <>{displayedText}</>;
              }
            } else if (line.text.includes('console')) {
              if (typedLength >= 7) { // 'console'
                highlightedText = (
                  <>
                    <span className={styles.variable}>console</span>
                    {typedLength > 7 && <span className={styles.punctuation}>.</span>}
                    {typedLength > 8 && (
                      <span className={styles.variable}>
                        {displayedText.substring(8, Math.min(typedLength, 11))}
                      </span>
                    )}
                    {/* 其余部分省略，根据需要添加 */}
                  </>
                );
              } else {
                highlightedText = <>{displayedText}</>;
              }
            } else if (line.text.includes('return')) {
              if (typedLength >= 6) { // 'return'
                highlightedText = (
                  <>
                    <span className={styles.keyword}>return</span>
                    {typedLength > 6 && ' '}
                    {typedLength > 7 && (
                      <span className={styles.variable}>
                        {displayedText.substring(7, Math.min(typedLength, 11))}
                      </span>
                    )}
                    {typedLength > 11 && <span className={styles.punctuation}>;</span>}
                  </>
                );
              } else {
                highlightedText = <>{displayedText}</>;
              }
            } else if (line.text === '}') {
              highlightedText = <span className={styles.punctuation}>{'}'}</span>;
            } else {
              highlightedText = <>{displayedText}</>;
            }
          }
          // CSS 高亮
          else if (language === 'CSS') {
            if (line.text.includes('.container')) {
              if (typedLength >= 1) {
                highlightedText = (
                  <>
                    <span className={styles.variable}>
                      {displayedText.substring(0, Math.min(typedLength, 10))}
                    </span>
                    {typedLength > 10 && ' '}
                    {typedLength > 11 && <span className={styles.punctuation}>{'{'}</span>}
                  </>
                );
              } else {
                highlightedText = <>{displayedText}</>;
              }
            } else if (line.text.includes('display') ||
                      line.text.includes('justify-content') ||
                      line.text.includes('align-items')) {
              // 简化处理CSS属性
              const colonIndex = displayedText.indexOf(':');
              if (colonIndex > 0) {
                highlightedText = (
                  <>
                    <span className={styles.keyword}>
                      {displayedText.substring(0, colonIndex)}
                    </span>
                    <span className={styles.punctuation}>:</span>
                    {displayedText.substring(colonIndex + 1, displayedText.indexOf(';') > 0 ?
                      displayedText.indexOf(';') : displayedText.length)}
                    {displayedText.indexOf(';') > 0 &&
                      <span className={styles.punctuation}>;</span>}
                  </>
                );
              } else {
                highlightedText = <>{displayedText}</>;
              }
            } else if (line.text === '}') {
              highlightedText = <span className={styles.punctuation}>{'}'}</span>;
            } else {
              highlightedText = <>{displayedText}</>;
            }
          }
          // PHP 高亮
          else if (language === 'PHP') {
            if (line.text.includes('function')) {
              if (typedLength >= 8) { // 'function'
                highlightedText = (
                  <>
                    <span className={styles.keyword}>function</span>
                    {typedLength > 8 && ' '}
                    {typedLength > 9 && (
                      <span className={styles.variable}>
                        {displayedText.substring(9, Math.min(typedLength, 25))}
                      </span>
                    )}
                    {typedLength > 25 && <span className={styles.punctuation}>()</span>}
                    {typedLength > 27 && ' '}
                    {typedLength > 28 && <span className={styles.punctuation}>{'{'}</span>}
                  </>
                );
              } else {
                highlightedText = <>{displayedText}</>;
              }
            } else if (line.text.includes('$result')) {
              if (typedLength >= 1) { // '$'
                highlightedText = (
                  <>
                    <span className={styles.variable}>
                      {displayedText.substring(0, Math.min(typedLength, 7))}
                    </span>
                    {typedLength > 7 && ' '}
                    {typedLength > 8 && <span className={styles.operator}>=</span>}
                    {typedLength > 9 && ' '}
                    {typedLength > 10 && (
                      <span className={styles.string}>
                        {displayedText.substring(10, Math.min(typedLength, 19))}
                      </span>
                    )}
                    {typedLength > 19 && <span className={styles.punctuation}>;</span>}
                  </>
                );
              } else {
                highlightedText = <>{displayedText}</>;
              }
            } else if (line.text.includes('return')) {
              if (typedLength >= 6) { // 'return'
                highlightedText = (
                  <>
                    <span className={styles.keyword}>return</span>
                    {typedLength > 6 && ' '}
                    {typedLength > 7 && (
                      <span className={styles.variable}>
                        {displayedText.substring(7, Math.min(typedLength, 14))}
                      </span>
                    )}
                    {typedLength > 14 && <span className={styles.punctuation}>;</span>}
                  </>
                );
              } else {
                highlightedText = <>{displayedText}</>;
              }
            } else if (line.text === '}') {
              highlightedText = <span className={styles.punctuation}>{'}'}</span>;
            } else {
              highlightedText = <>{displayedText}</>;
            }
          }
          // 默认情况
          else {
            highlightedText = <>{displayedText}</>;
          }

          return (
            <div key={lineIndex} className={styles.codeLine} style={{ textAlign: 'left' }}>
              {line.indent > 0 && <span>{indentSpaces}</span>}
              {highlightedText}
              {showCursor && <span className={styles.cursor}></span>}
            </div>
          );
        }

        // 已完成的行
        const indentSpaces = '\u00A0\u00A0'.repeat(line.indent);
        return (
          <div key={lineIndex} className={styles.codeLine} style={{ textAlign: 'left' }}>
            {line.indent > 0 && <span>{indentSpaces}</span>}
            {getHighlightedText(line.text)}
          </div>
        );
      });
    };

    // 添加语法高亮的辅助函数
    const getHighlightedText = (text: string) => {
      const language = currentExample.language;

      // JavaScript 高亮
      if (language === 'JavaScript') {
        if (text.includes('const')) {
          return <><span className={styles.keyword}>const</span> <span className={styles.variable}>createExperience</span> <span className={styles.operator}>=</span> <span className={styles.punctuation}>()</span> <span className={styles.operator}>=&gt;</span> <span className={styles.punctuation}>{'{'}</span></>;
        } else if (text.includes('return')) {
          return <><span className={styles.keyword}>return</span> <span className={styles.string}>"Amazing"</span><span className={styles.punctuation}>;</span></>;
        } else if (text === '}') {
          return <><span className={styles.punctuation}>{'}'}</span></>;
        }
      }

      // Python 高亮
      else if (language === 'Python') {
        if (text.includes('def')) {
          return <><span className={styles.keyword}>def</span> <span className={styles.variable}>create_experience</span><span className={styles.punctuation}>()</span><span className={styles.punctuation}>:</span></>;
        } else if (text.includes('return')) {
          return <><span className={styles.keyword}>return</span> <span className={styles.string}>"Amazing"</span></>;
        }
      }

      // TypeScript 高亮
      else if (language === 'TypeScript') {
        if (text.includes('function')) {
          return <><span className={styles.keyword}>function</span> <span className={styles.variable}>processData</span><span className={styles.operator}>&lt;</span><span className={styles.variable}>T</span><span className={styles.operator}>&gt;</span><span className={styles.punctuation}>(</span><span className={styles.variable}>data</span><span className={styles.punctuation}>:</span> <span className={styles.variable}>T</span><span className={styles.punctuation}>)</span><span className={styles.punctuation}>:</span> <span className={styles.variable}>T</span> <span className={styles.punctuation}>{'{'}</span></>;
        } else if (text.includes('console')) {
          return <><span className={styles.variable}>console</span><span className={styles.punctuation}>.</span><span className={styles.variable}>log</span><span className={styles.punctuation}>(</span><span className={styles.string}>"Processing..."</span><span className={styles.punctuation}>)</span><span className={styles.punctuation}>;</span></>;
        } else if (text.includes('return')) {
          return <><span className={styles.keyword}>return</span> <span className={styles.variable}>data</span><span className={styles.punctuation}>;</span></>;
        } else if (text === '}') {
          return <><span className={styles.punctuation}>{'}'}</span></>;
        }
      }

      // CSS 高亮
      else if (language === 'CSS') {
        if (text.includes('.container')) {
          return <><span className={styles.variable}>.container</span> <span className={styles.punctuation}>{'{'}</span></>;
        } else if (text.includes('display')) {
          return <><span className={styles.keyword}>display</span><span className={styles.punctuation}>:</span> <span className={styles.string}>flex</span><span className={styles.punctuation}>;</span></>;
        } else if (text.includes('justify-content')) {
          return <><span className={styles.keyword}>justify-content</span><span className={styles.punctuation}>:</span> <span className={styles.string}>center</span><span className={styles.punctuation}>;</span></>;
        } else if (text.includes('align-items')) {
          return <><span className={styles.keyword}>align-items</span><span className={styles.punctuation}>:</span> <span className={styles.string}>center</span><span className={styles.punctuation}>;</span></>;
        } else if (text === '}') {
          return <><span className={styles.punctuation}>{'}'}</span></>;
        }
      }

      // PHP 高亮
      else if (language === 'PHP') {
        if (text.includes('function')) {
          return <><span className={styles.keyword}>function</span> <span className={styles.variable}>createExperience</span><span className={styles.punctuation}>()</span> <span className={styles.punctuation}>{'{'}</span></>;
        } else if (text.includes('$result')) {
          return <><span className={styles.variable}>$result</span> <span className={styles.operator}>=</span> <span className={styles.string}>"Amazing"</span><span className={styles.punctuation}>;</span></>;
        } else if (text.includes('return')) {
          return <><span className={styles.keyword}>return</span> <span className={styles.variable}>$result</span><span className={styles.punctuation}>;</span></>;
        } else if (text === '}') {
          return <><span className={styles.punctuation}>{'}'}</span></>;
        }
      }

      // 默认情况
      return <>{text}</>;
    };

    return (
      <div className={styles.codeSnippet}>
        <div className={styles.languageLabel}>{currentExample.language}</div>
        <pre className={styles.codeBlock}>
          <code>
            {renderCodeLines()}
          </code>
        </pre>
      </div>
    );
  };

  return (
    <AnimatePresence mode="sync">
      {visible && (
        <motion.div
          className={styles.tagline}
          initial="hidden"
          animate="visible"
          exit="exit"
          variants={containerVariants}
          layout={false}
          ref={containerRef}
          onMouseMove={handleMouseMove}
          onMouseLeave={handleMouseLeave}
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            pointerEvents: visible ? 'auto' : 'none'
          }}
        >
          <div className={styles.taglineBackground}></div>

          {/* 浮动元素 */}
          {floatingElements.map((el, index) => (
            <motion.div
              key={el.id}
              className={styles.floatingElement}
              style={{
                left: `${el.x}%`,
                top: `${el.y}%`,
                width: `${el.size}px`,
                height: `${el.size}px`
              }}
              custom={index}
              variants={floatingVariants}
              animate="animate"
            />
          ))}

          <div className={styles.taglineContent}>
            <motion.div
              className={styles.taglineMain}
              variants={childVariants}
              style={{
                perspective: 1000,
                transformStyle: "preserve-3d"
              }}
            >
              <motion.h2
                className={styles.taglineHeading}
                variants={childVariants}
                style={{
                  rotateX: springRotateX,
                  rotateY: springRotateY,
                  transformStyle: "preserve-3d"
                }}
              >
                <Typewriter
                  texts={['创造优雅的数字体验', '构建直观的用户界面', '开发高效的应用程序']}
                  typingSpeed={80}
                  deletingSpeed={40}
                  delayAfterType={3000}
                />
              </motion.h2>
              <motion.p
                className={styles.taglineSubheading}
                variants={childVariants}
                style={{
                  rotateX: springRotateX,
                  rotateY: springRotateY,
                  transformStyle: "preserve-3d"
                }}
              >
                <span className={styles.taglineHighlight}>全栈开发</span>，专注于构建直观、高效且美观的用户界面
              </motion.p>
              <motion.div className={styles.taglineActions} variants={childVariants}>
                <motion.div
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <Link href="/projects" className={styles.taglinePrimaryButton}>
                    查看作品
                    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={styles.taglineButtonIcon}>
                      <line x1="5" y1="12" x2="19" y2="12"></line>
                      <polyline points="12 5 19 12 12 19"></polyline>
                    </svg>
                  </Link>
                </motion.div>
                <motion.div
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <Link href="/contact" className={styles.taglineSecondaryButton}>
                    联系我
                  </Link>
                </motion.div>
              </motion.div>
            </motion.div>

            <motion.div
              className={styles.taglineVisual}
              variants={childVariants}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{
                duration: 0.8,
                delay: 0.3,
                ease: [0.16, 1, 0.3, 1]
              }}
              style={{
                rotateX: springRotateX,
                rotateY: springRotateY,
                transformStyle: "preserve-3d"
              }}
            >
              <motion.div
                className={styles.taglineImageContainer}
                whileHover={{
                  scale: 1.05,
                  boxShadow: "0 15px 30px rgba(0, 0, 0, 0.15)"
                }}
                transition={{ duration: 0.3 }}
              >
                <motion.div
                  className={styles.taglineImage}
                  animate={{
                    opacity: [0.9, 1, 0.9]
                  }}
                  transition={{
                    duration: 5,
                    repeat: Infinity,
                    repeatType: "reverse"
                  }}
                >
                  <CodeSnippet />
                </motion.div>
              </motion.div>
            </motion.div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default Tagline;
