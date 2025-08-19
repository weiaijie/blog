/**
 * 主题提供者组件测试
 * 测试主题切换功能和本地存储
 */

import React from 'react'
import { render, screen, fireEvent, act } from '@testing-library/react'
import { ThemeProvider, useTheme } from '@/contexts/ThemeContext'

// 测试组件，用于测试 useTheme hook
const TestComponent = () => {
  const { theme, toggleTheme } = useTheme()
  
  return (
    <div>
      <div data-testid="current-theme">{theme}</div>
      <button data-testid="toggle-button" onClick={toggleTheme}>
        Toggle Theme
      </button>
    </div>
  )
}

describe('ThemeProvider', () => {
  beforeEach(() => {
    // 清除 localStorage mock
    localStorage.clear()
    jest.clearAllMocks()
  })

  it('应该提供默认的浅色主题', () => {
    render(
      <ThemeProvider>
        <TestComponent />
      </ThemeProvider>
    )

    expect(screen.getByTestId('current-theme')).toHaveTextContent('light')
  })

  it('应该能够切换主题', () => {
    render(
      <ThemeProvider>
        <TestComponent />
      </ThemeProvider>
    )

    const toggleButton = screen.getByTestId('toggle-button')
    const themeDisplay = screen.getByTestId('current-theme')

    // 初始状态应该是浅色主题
    expect(themeDisplay).toHaveTextContent('light')

    // 点击切换按钮
    act(() => {
      fireEvent.click(toggleButton)
    })

    // 应该切换到深色主题
    expect(themeDisplay).toHaveTextContent('dark')

    // 再次点击切换按钮
    act(() => {
      fireEvent.click(toggleButton)
    })

    // 应该切换回浅色主题
    expect(themeDisplay).toHaveTextContent('light')
  })

  it('应该将主题偏好保存到 localStorage', () => {
    render(
      <ThemeProvider>
        <TestComponent />
      </ThemeProvider>
    )

    const toggleButton = screen.getByTestId('toggle-button')

    // 切换到深色主题
    act(() => {
      fireEvent.click(toggleButton)
    })

    // 检查 localStorage 是否被调用
    expect(localStorage.setItem).toHaveBeenCalledWith('theme', 'dark')
  })

  it('应该从 localStorage 加载保存的主题', () => {
    // 模拟 localStorage 中已保存深色主题
    localStorage.getItem.mockReturnValue('dark')

    render(
      <ThemeProvider>
        <TestComponent />
      </ThemeProvider>
    )

    // 应该加载保存的深色主题
    expect(screen.getByTestId('current-theme')).toHaveTextContent('dark')
  })

  it('当 localStorage 中的值无效时应该使用默认主题', () => {
    // 模拟 localStorage 中的无效值
    localStorage.getItem.mockReturnValue('invalid-theme')

    render(
      <ThemeProvider>
        <TestComponent />
      </ThemeProvider>
    )

    // 应该使用默认的浅色主题
    expect(screen.getByTestId('current-theme')).toHaveTextContent('light')
  })

  it('应该在 document.documentElement 上设置正确的 data-theme 属性', () => {
    render(
      <ThemeProvider>
        <TestComponent />
      </ThemeProvider>
    )

    // 初始状态应该有 light 主题
    expect(document.documentElement.getAttribute('data-theme')).toBe('light')

    const toggleButton = screen.getByTestId('toggle-button')

    // 切换到深色主题
    act(() => {
      fireEvent.click(toggleButton)
    })

    // 应该有 dark 主题
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark')
  })

  it('在没有 ThemeProvider 的情况下使用 useTheme 应该抛出错误', () => {
    // 捕获控制台错误以避免测试输出中的错误信息
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {})

    expect(() => {
      render(<TestComponent />)
    }).toThrow('useTheme must be used within a ThemeProvider')

    consoleSpy.mockRestore()
  })
})
