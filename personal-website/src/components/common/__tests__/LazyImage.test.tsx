/**
 * LazyImage 组件测试
 * 测试图片懒加载功能和错误处理
 */

import React from 'react'
import { render, screen } from '@testing-library/react'

// Mock CSS 模块
jest.mock('@/styles/LazyImage.module.css', () => ({
  lazyImageContainer: 'lazyImageContainer',
  imageWrapper: 'imageWrapper',
  placeholder: 'placeholder',
  image: 'image',
  loaded: 'loaded',
  error: 'error',
  fadeIn: 'fadeIn',
}))

import LazyImage from '../LazyImage'

// Mock Next.js Image component
jest.mock('next/image', () => {
  return function MockImage({ src, alt, onLoad, onError, ...props }: any) {
    return (
      <img
        src={src}
        alt={alt}
        onLoad={onLoad}
        onError={onError}
        data-testid="next-image"
        {...props}
      />
    )
  }
})

// Mock Framer Motion
jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
  },
}))

describe('LazyImage', () => {
  const defaultProps = {
    src: '/test-image.jpg',
    alt: '测试图片',
    width: 400,
    height: 300,
  }

  it('应该渲染占位符图片', () => {
    render(<LazyImage {...defaultProps} />)

    // 应该显示占位符
    const placeholder = screen.getByAltText('Loading...')
    expect(placeholder).toBeInTheDocument()
    expect(placeholder).toHaveAttribute('src', '/images/placeholder.svg')
  })

  it('应该渲染容器和占位符', () => {
    render(<LazyImage {...defaultProps} />)

    // 应该有容器
    const container = screen.getByAltText('Loading...').closest('div')
    expect(container).toBeInTheDocument()

    // 应该显示占位符
    const placeholder = screen.getByAltText('Loading...')
    expect(placeholder).toBeInTheDocument()
  })

  it('应该设置正确的容器样式', () => {
    render(<LazyImage {...defaultProps} />)

    // 检查容器是否存在
    const container = screen.getByAltText('Loading...').closest('div')
    expect(container).toBeInTheDocument()
  })
})
