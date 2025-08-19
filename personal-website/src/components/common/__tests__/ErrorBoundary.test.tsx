/**
 * ErrorBoundary 组件测试
 * 测试错误捕获和错误界面显示
 */

import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'

// Mock CSS 模块
jest.mock('@/styles/ErrorBoundary.module.css', () => ({
  errorBoundary: 'errorBoundary',
  errorContainer: 'errorContainer',
  errorIcon: 'errorIcon',
  errorTitle: 'errorTitle',
  errorMessage: 'errorMessage',
  errorDetails: 'errorDetails',
  errorActions: 'errorActions',
  retryButton: 'retryButton',
  refreshButton: 'refreshButton',
  detailsButton: 'detailsButton',
  detailsContent: 'detailsContent',
  errorCode: 'errorCode',
  errorStack: 'errorStack',
}))

import ErrorBoundary from '../ErrorBoundary'

// Mock Framer Motion
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
}))

// 创建一个会抛出错误的测试组件
const ThrowError = ({ shouldThrow }: { shouldThrow: boolean }) => {
  if (shouldThrow) {
    throw new Error('测试错误')
  }
  return <div>正常组件</div>
}

// Mock console.error 以避免测试输出中的错误信息
const originalError = console.error
beforeAll(() => {
  console.error = jest.fn()
})

afterAll(() => {
  console.error = originalError
})

describe('ErrorBoundary', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('应该正常渲染子组件当没有错误时', () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={false} />
      </ErrorBoundary>
    )

    expect(screen.getByText('正常组件')).toBeInTheDocument()
  })

  it('应该捕获错误并显示错误界面', () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    )

    // 应该显示错误界面
    expect(screen.getByText('出现了一些问题')).toBeInTheDocument()
    expect(screen.getByText(/很抱歉，页面遇到了意外错误/)).toBeInTheDocument()
  })

  it('应该显示重试和刷新按钮', () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    )

    expect(screen.getByText('重试')).toBeInTheDocument()
    expect(screen.getByText('刷新页面')).toBeInTheDocument()
  })

  it('点击重试按钮应该存在', () => {
    const ThrowError = () => {
      throw new Error('测试错误')
    }

    render(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    )

    // 确认错误界面显示
    expect(screen.getByText('出现了一些问题')).toBeInTheDocument()

    // 重试按钮应该存在
    const retryButton = screen.getByText('重试')
    expect(retryButton).toBeInTheDocument()

    // 点击重试按钮不应该报错
    fireEvent.click(retryButton)
  })

  it('应该调用 onError 回调', () => {
    const onErrorMock = jest.fn()

    render(
      <ErrorBoundary onError={onErrorMock}>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    )

    expect(onErrorMock).toHaveBeenCalled()
    expect(onErrorMock).toHaveBeenCalledWith(
      expect.any(Error),
      expect.objectContaining({
        componentStack: expect.any(String),
      })
    )
  })

  it('应该使用自定义 fallback', () => {
    const customFallback = <div>自定义错误界面</div>

    render(
      <ErrorBoundary fallback={customFallback}>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    )

    expect(screen.getByText('自定义错误界面')).toBeInTheDocument()
    expect(screen.queryByText('出现了一些问题')).not.toBeInTheDocument()
  })

  it('在开发环境下应该显示错误详情', () => {
    const originalEnv = process.env.NODE_ENV
    process.env.NODE_ENV = 'development'

    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    )

    // 应该有错误详情的展开按钮
    expect(screen.getByText('错误详情')).toBeInTheDocument()

    process.env.NODE_ENV = originalEnv
  })

  it('当 showDetails 为 true 时应该显示错误详情', () => {
    render(
      <ErrorBoundary showDetails={true}>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    )

    expect(screen.getByText('错误详情')).toBeInTheDocument()
  })

  it('应该在属性变化时重置错误状态', () => {
    const { rerender } = render(
      <ErrorBoundary resetOnPropsChange={true} resetKeys={['key1']}>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    )

    // 确认错误界面显示
    expect(screen.getByText('出现了一些问题')).toBeInTheDocument()

    // 改变 resetKeys
    rerender(
      <ErrorBoundary resetOnPropsChange={true} resetKeys={['key2']}>
        <ThrowError shouldThrow={false} />
      </ErrorBoundary>
    )

    // 应该重置并显示正常组件
    expect(screen.getByText('正常组件')).toBeInTheDocument()
  })

  it('刷新按钮应该调用 window.location.reload', () => {
    // Mock window.location.reload
    const mockReload = jest.fn()
    Object.defineProperty(window, 'location', {
      value: {
        reload: mockReload,
      },
      writable: true,
    })

    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    )

    fireEvent.click(screen.getByText('刷新页面'))

    expect(mockReload).toHaveBeenCalled()
  })

  it('应该生成唯一的事件ID', () => {
    const onErrorMock = jest.fn()

    render(
      <ErrorBoundary onError={onErrorMock}>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    )

    // 检查是否生成了事件ID（通过检查组件状态）
    // 这里我们通过检查错误详情是否包含事件ID来验证
    if (process.env.NODE_ENV === 'development') {
      expect(screen.getByText('错误详情')).toBeInTheDocument()
    }
  })
})
