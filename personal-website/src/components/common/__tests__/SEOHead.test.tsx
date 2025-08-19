/**
 * SEOHead 组件测试
 * 测试 meta 标签生成和 SEO 优化功能
 */

import React from 'react'
import { render } from '@testing-library/react'
import SEOHead from '../SEOHead'

describe('SEOHead', () => {
  const defaultProps = {
    title: '测试页面',
    description: '这是一个测试页面的描述',
  }

  beforeEach(() => {
    // 重置环境变量
    delete process.env.NEXT_PUBLIC_SITE_URL
  })

  it('应该渲染基本的 meta 标签', () => {
    const { container } = render(<SEOHead {...defaultProps} />)

    // 检查 title 标签
    expect(container.querySelector('title')).toHaveTextContent('测试页面 - 许辉的个人网站')

    // 检查 description meta 标签
    expect(container.querySelector('meta[name="description"]')).toHaveAttribute(
      'content',
      '这是一个测试页面的描述'
    )
  })

  it('应该生成正确的 Open Graph 标签', () => {
    const props = {
      ...defaultProps,
      type: 'article' as const,
      image: '/test-image.jpg',
    }

    const { container } = render(<SEOHead {...props} />)

    // 检查 Open Graph 标签
    expect(container.querySelector('meta[property="og:title"]')).toHaveAttribute(
      'content',
      '测试页面 - 许辉的个人网站'
    )
    expect(container.querySelector('meta[property="og:description"]')).toHaveAttribute(
      'content',
      '这是一个测试页面的描述'
    )
    expect(container.querySelector('meta[property="og:type"]')).toHaveAttribute(
      'content',
      'article'
    )
    expect(container.querySelector('meta[property="og:image"]')).toHaveAttribute(
      'content',
      'http://localhost:3000/test-image.jpg'
    )
  })

  it('应该生成正确的 Twitter Card 标签', () => {
    const props = {
      ...defaultProps,
      image: '/test-image.jpg',
    }

    const { container } = render(<SEOHead {...props} />)

    // 检查 Twitter Card 标签
    expect(container.querySelector('meta[name="twitter:card"]')).toHaveAttribute(
      'content',
      'summary_large_image'
    )
    expect(container.querySelector('meta[name="twitter:title"]')).toHaveAttribute(
      'content',
      '测试页面 - 许辉的个人网站'
    )
    expect(container.querySelector('meta[name="twitter:description"]')).toHaveAttribute(
      'content',
      '这是一个测试页面的描述'
    )
    expect(container.querySelector('meta[name="twitter:image"]')).toHaveAttribute(
      'content',
      'http://localhost:3000/test-image.jpg'
    )
  })

  it('应该处理关键词', () => {
    const props = {
      ...defaultProps,
      keywords: ['测试', '关键词', 'SEO'],
    }

    const { container } = render(<SEOHead {...props} />)

    expect(container.querySelector('meta[name="keywords"]')).toHaveAttribute(
      'content',
      '测试, 关键词, SEO'
    )
  })

  it('应该生成文章类型的结构化数据', () => {
    const props = {
      ...defaultProps,
      type: 'article' as const,
      publishedTime: '2024-08-12T10:00:00Z',
      author: '许辉',
      section: '技术',
      tags: ['React', 'Next.js'],
    }

    const { container } = render(<SEOHead {...props} />)

    // 检查 article 特定的 meta 标签
    expect(container.querySelector('meta[property="article:published_time"]')).toHaveAttribute(
      'content',
      '2024-08-12T10:00:00Z'
    )
    expect(container.querySelector('meta[property="article:author"]')).toHaveAttribute(
      'content',
      '许辉'
    )

    const structuredData = container.querySelector('script[type="application/ld+json"]')
    expect(structuredData).toBeTruthy()

    const jsonData = JSON.parse(structuredData?.textContent || '{}')
    expect(jsonData['@type']).toBe('WebPage')
    expect(jsonData.name).toBe('测试页面 - 许辉的个人网站')
    expect(jsonData.description).toBe('这是一个测试页面的描述')
  })

  it('应该生成网站类型的结构化数据', () => {
    const props = {
      ...defaultProps,
      type: 'website' as const,
    }

    const { container } = render(<SEOHead {...props} />)

    const structuredData = container.querySelector('script[type="application/ld+json"]')
    expect(structuredData).toBeTruthy()

    const jsonData = JSON.parse(structuredData?.textContent || '{}')
    expect(jsonData['@type']).toBe('WebPage')
    expect(jsonData.name).toBe('测试页面 - 许辉的个人网站')
    expect(jsonData.description).toBe('这是一个测试页面的描述')
  })

  it('应该使用环境变量中的网站 URL', () => {
    process.env.NEXT_PUBLIC_SITE_URL = 'https://example.com'

    const props = {
      ...defaultProps,
      image: '/test-image.jpg',
    }

    const { container } = render(<SEOHead {...props} />)

    expect(container.querySelector('meta[property="og:image"]')).toHaveAttribute(
      'content',
      'http://localhost:3000/test-image.jpg'
    )
  })

  it('应该使用默认图片当没有提供图片时', () => {
    const { container } = render(<SEOHead {...defaultProps} />)

    expect(container.querySelector('meta[property="og:image"]')).toHaveAttribute(
      'content',
      'http://localhost:3000/images/og-default.svg'
    )
  })

  it('应该处理绝对 URL 的图片', () => {
    const props = {
      ...defaultProps,
      image: 'https://example.com/external-image.jpg',
    }

    const { container } = render(<SEOHead {...props} />)

    expect(container.querySelector('meta[property="og:image"]')).toHaveAttribute(
      'content',
      'https://example.com/external-image.jpg'
    )
  })
})
