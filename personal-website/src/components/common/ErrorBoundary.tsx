/**
 * ErrorBoundary.tsx
 *
 * 描述：React错误边界组件，用于捕获和处理组件错误
 *
 * 功能：
 * - 捕获子组件中的JavaScript错误
 * - 显示友好的错误界面
 * - 记录错误信息用于调试
 * - 提供错误恢复机制
 * - 支持不同的错误显示模式
 *
 * 主要接口：
 * - ErrorBoundaryProps：错误边界组件属性
 * - ErrorBoundaryState：错误边界状态
 * - ErrorBoundary：错误边界组件类
 */

import React, { Component, ReactNode } from 'react';
import { motion } from 'framer-motion';
import styles from '@/styles/ErrorBoundary.module.css';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
  showDetails?: boolean;
  resetOnPropsChange?: boolean;
  resetKeys?: Array<string | number>;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: React.ErrorInfo | null;
  eventId: string | null;
}

class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  private resetTimeoutId: number | null = null;

  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      eventId: null,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    // 更新状态以显示错误界面
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // 记录错误信息
    this.setState({
      error,
      errorInfo,
      eventId: this.generateEventId(),
    });

    // 调用外部错误处理函数
    this.props.onError?.(error, errorInfo);

    // 在开发环境下输出详细错误信息
    if (process.env.NODE_ENV === 'development') {
      console.group('🚨 Error Boundary Caught an Error');
      console.error('Error:', error);
      console.error('Error Info:', errorInfo);
      console.error('Component Stack:', errorInfo.componentStack);
      console.groupEnd();
    }

    // 在生产环境下可以发送错误到监控服务
    if (process.env.NODE_ENV === 'production') {
      this.reportErrorToService(error, errorInfo);
    }
  }

  componentDidUpdate(prevProps: ErrorBoundaryProps) {
    const { resetOnPropsChange, resetKeys } = this.props;
    const { hasError } = this.state;

    // 如果有错误且启用了属性变化重置
    if (hasError && resetOnPropsChange) {
      // 检查重置键是否发生变化
      if (resetKeys) {
        const prevResetKeys = prevProps.resetKeys || [];
        const hasResetKeyChanged = resetKeys.some(
          (key, index) => key !== prevResetKeys[index]
        );
        
        if (hasResetKeyChanged) {
          this.resetErrorBoundary();
        }
      }
    }
  }

  componentWillUnmount() {
    if (this.resetTimeoutId) {
      clearTimeout(this.resetTimeoutId);
    }
  }

  // 生成错误事件ID
  private generateEventId(): string {
    return `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  // 上报错误到监控服务
  private reportErrorToService(error: Error, errorInfo: React.ErrorInfo) {
    // 这里可以集成Sentry、LogRocket等错误监控服务
    // 示例：
    // Sentry.captureException(error, {
    //   contexts: {
    //     react: {
    //       componentStack: errorInfo.componentStack,
    //     },
    //   },
    // });
  }

  // 重置错误边界
  private resetErrorBoundary = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      eventId: null,
    });
  };

  // 自动重试
  private handleRetry = () => {
    this.resetErrorBoundary();
  };

  // 刷新页面
  private handleRefresh = () => {
    window.location.reload();
  };

  render() {
    const { hasError, error, errorInfo, eventId } = this.state;
    const { children, fallback, showDetails = false } = this.props;

    if (hasError) {
      // 如果提供了自定义fallback，使用它
      if (fallback) {
        return fallback;
      }

      // 默认错误界面
      return (
        <div className={styles.errorBoundary}>
          <motion.div
            className={styles.errorContainer}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <div className={styles.errorIcon}>
              <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10"/>
                <line x1="12" y1="8" x2="12" y2="12"/>
                <line x1="12" y1="16" x2="12.01" y2="16"/>
              </svg>
            </div>
            
            <h2 className={styles.errorTitle}>出现了一些问题</h2>
            <p className={styles.errorMessage}>
              很抱歉，页面遇到了意外错误。我们已经记录了这个问题，请稍后再试。
            </p>

            {/* 错误详情（开发环境或启用详情时显示） */}
            {(showDetails || process.env.NODE_ENV === 'development') && error && (
              <details className={styles.errorDetails}>
                <summary>错误详情</summary>
                <div className={styles.errorInfo}>
                  <p><strong>错误信息:</strong> {error.message}</p>
                  <p><strong>错误类型:</strong> {error.name}</p>
                  {eventId && <p><strong>事件ID:</strong> {eventId}</p>}
                  {error.stack && (
                    <div>
                      <strong>错误堆栈:</strong>
                      <pre className={styles.errorStack}>{error.stack}</pre>
                    </div>
                  )}
                  {errorInfo?.componentStack && (
                    <div>
                      <strong>组件堆栈:</strong>
                      <pre className={styles.errorStack}>{errorInfo.componentStack}</pre>
                    </div>
                  )}
                </div>
              </details>
            )}

            {/* 操作按钮 */}
            <div className={styles.errorActions}>
              <button
                className={styles.retryButton}
                onClick={this.handleRetry}
              >
                重试
              </button>
              <button
                className={styles.refreshButton}
                onClick={this.handleRefresh}
              >
                刷新页面
              </button>
            </div>
          </motion.div>
        </div>
      );
    }

    return children;
  }
}

export default ErrorBoundary;
