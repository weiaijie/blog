/**
 * LazyImage.tsx
 *
 * 描述：图片懒加载组件，优化页面性能
 *
 * 功能：
 * - 使用Intersection Observer API实现图片懒加载
 * - 支持占位符和加载状态
 * - 支持错误处理和回退图片
 * - 支持响应式图片
 * - 提供平滑的加载动画
 *
 * 主要接口：
 * - LazyImageProps：图片组件属性接口
 * - LazyImage：懒加载图片组件
 */

import { useState, useRef, useEffect } from 'react';
import Image from 'next/image';
import { motion } from 'framer-motion';
import styles from '@/styles/LazyImage.module.css';

interface LazyImageProps {
  src: string;
  alt: string;
  width?: number;
  height?: number;
  className?: string;
  placeholder?: string;
  fallback?: string;
  priority?: boolean;
  quality?: number;
  sizes?: string;
  fill?: boolean;
  objectFit?: 'contain' | 'cover' | 'fill' | 'none' | 'scale-down';
  onLoad?: () => void;
  onError?: () => void;
}

export default function LazyImage({
  src,
  alt,
  width,
  height,
  className = '',
  placeholder = '/images/placeholder.svg',
  fallback = '/images/image-error.svg',
  priority = false,
  quality = 75,
  sizes,
  fill = false,
  objectFit = 'cover',
  onLoad,
  onError
}: LazyImageProps) {
  const [isLoaded, setIsLoaded] = useState(false);
  const [isInView, setIsInView] = useState(false);
  const [hasError, setHasError] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const imgRef = useRef<HTMLDivElement>(null);

  // 使用Intersection Observer监听图片是否进入视口
  useEffect(() => {
    if (priority) {
      // 如果是优先级图片，立即加载
      setIsInView(true);
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setIsInView(true);
            setIsLoading(true);
            observer.unobserve(entry.target);
          }
        });
      },
      {
        rootMargin: '50px', // 提前50px开始加载
        threshold: 0.1
      }
    );

    if (imgRef.current) {
      observer.observe(imgRef.current);
    }

    return () => {
      if (imgRef.current) {
        observer.unobserve(imgRef.current);
      }
    };
  }, [priority]);

  // 处理图片加载完成
  const handleLoad = () => {
    setIsLoaded(true);
    setIsLoading(false);
    onLoad?.();
  };

  // 处理图片加载错误
  const handleError = () => {
    setHasError(true);
    setIsLoading(false);
    onError?.();
  };

  // 动画变体
  const imageVariants = {
    hidden: { opacity: 0, scale: 1.1 },
    visible: {
      opacity: 1,
      scale: 1,
      transition: {
        duration: 0.6,
        ease: [0.25, 0.1, 0.25, 1.0]
      }
    }
  };

  const placeholderVariants = {
    visible: { opacity: 1 },
    hidden: {
      opacity: 0,
      transition: {
        duration: 0.3
      }
    }
  };

  return (
    <div
      ref={imgRef}
      className={`${styles.lazyImageContainer} ${className}`}
      style={{
        width: fill ? '100%' : width,
        height: fill ? '100%' : height,
        position: fill ? 'relative' : 'relative'
      }}
    >
      {/* 占位符 */}
      {!isLoaded && !hasError && (
        <motion.div
          className={styles.placeholder}
          variants={placeholderVariants}
          initial="visible"
          animate={isLoaded ? "hidden" : "visible"}
        >
          {isInView && isLoading ? (
            <div className={styles.loadingSpinner}>
              <div className={styles.spinner}></div>
            </div>
          ) : (
            <Image
              src={placeholder}
              alt="Loading..."
              fill={fill}
              width={!fill ? width : undefined}
              height={!fill ? height : undefined}
              className={styles.placeholderImage}
              style={{ objectFit }}
            />
          )}
        </motion.div>
      )}

      {/* 实际图片 */}
      {isInView && !hasError && (
        <motion.div
          className={styles.imageWrapper}
          variants={imageVariants}
          initial="hidden"
          animate={isLoaded ? "visible" : "hidden"}
        >
          <Image
            src={src}
            alt={alt}
            fill={fill}
            width={!fill ? width : undefined}
            height={!fill ? height : undefined}
            quality={quality}
            sizes={sizes}
            priority={priority}
            className={styles.image}
            style={{ objectFit }}
            onLoad={handleLoad}
            onError={handleError}
          />
        </motion.div>
      )}

      {/* 错误回退图片 */}
      {hasError && (
        <motion.div
          className={styles.errorWrapper}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.3 }}
        >
          <Image
            src={fallback}
            alt="Failed to load image"
            fill={fill}
            width={!fill ? width : undefined}
            height={!fill ? height : undefined}
            className={styles.errorImage}
            style={{ objectFit }}
          />
        </motion.div>
      )}
    </div>
  );
}
