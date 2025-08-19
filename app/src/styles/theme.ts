/**
 * 主题配置文件
 *
 * 这是应用的核心主题系统配置，提供：
 *
 * 主要功能：
 * 1. 设计系统规范 - 统一的间距、圆角、阴影等设计标准
 * 2. 主题切换支持 - 明亮和暗黑主题的完整配置
 * 3. 类型安全 - 完整的TypeScript类型定义
 * 4. 响应式设计 - 适配不同屏幕尺寸的设计规范
 * 5. 可扩展性 - 易于添加新的主题变量和配置
 *
 * 设计原则：
 * - 遵循Material Design和iOS设计规范
 * - 保持一致性和可预测性
 * - 支持无障碍访问
 * - 易于维护和扩展
 */

import { Colors, LightTheme, DarkTheme } from './colors';
import { Typography, FontFamily, FontSize, FontWeight } from './typography';

// ==================== 设计系统基础配置 ====================

/**
 * 间距系统
 *
 * 提供统一的间距规范，确保界面元素的一致性
 * 基于8px网格系统，符合Material Design规范
 */
export const Spacing = {
  xs: 4,      // 极小间距 - 用于紧密相关的元素
  sm: 8,      // 小间距 - 用于相关元素之间
  md: 16,     // 中等间距 - 默认间距，最常用
  lg: 24,     // 大间距 - 用于分组元素
  xl: 32,     // 超大间距 - 用于主要分区
  '2xl': 48,  // 2倍超大间距 - 用于页面级分隔
  '3xl': 64,  // 3倍超大间距 - 用于重要分区
  '4xl': 96,  // 4倍超大间距 - 用于页面顶部/底部
  '5xl': 128, // 5倍超大间距 - 用于特殊布局
} as const;

/**
 * 圆角系统
 *
 * 提供统一的圆角规范，创建现代化的界面风格
 * 支持从无圆角到完全圆形的各种需求
 */
export const BorderRadius = {
  none: 0,      // 无圆角 - 用于严肃、正式的界面
  sm: 4,        // 小圆角 - 用于按钮、输入框等
  md: 8,        // 中等圆角 - 用于卡片、容器等
  lg: 12,       // 大圆角 - 用于重要元素
  xl: 16,       // 超大圆角 - 用于特殊设计
  '2xl': 24,    // 2倍超大圆角 - 用于大型容器
  '3xl': 32,    // 3倍超大圆角 - 用于特殊效果
  full: 9999,   // 完全圆形 - 用于头像、徽章等
} as const;

// 阴影系统
export const Shadow = {
  none: {
    shadowColor: 'transparent',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0,
    shadowRadius: 0,
    elevation: 0,
  },
  sm: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.18,
    shadowRadius: 1.0,
    elevation: 1,
  },
  md: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.23,
    shadowRadius: 2.62,
    elevation: 4,
  },
  lg: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.30,
    shadowRadius: 4.65,
    elevation: 8,
  },
  xl: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.37,
    shadowRadius: 7.49,
    elevation: 12,
  },
  '2xl': {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.51,
    shadowRadius: 13.16,
    elevation: 20,
  },
} as const;

// 边框宽度
export const BorderWidth = {
  none: 0,
  thin: 0.5,
  base: 1,
  thick: 2,
  thicker: 4,
} as const;

// 透明度
export const Opacity = {
  0: 0,
  5: 0.05,
  10: 0.1,
  20: 0.2,
  25: 0.25,
  30: 0.3,
  40: 0.4,
  50: 0.5,
  60: 0.6,
  70: 0.7,
  75: 0.75,
  80: 0.8,
  90: 0.9,
  95: 0.95,
  100: 1,
} as const;

// Z-Index层级
export const ZIndex = {
  hide: -1,
  auto: 'auto',
  base: 0,
  docked: 10,
  dropdown: 1000,
  sticky: 1100,
  banner: 1200,
  overlay: 1300,
  modal: 1400,
  popover: 1500,
  skipLink: 1600,
  toast: 1700,
  tooltip: 1800,
} as const;

// 动画配置
export const Animation = {
  duration: {
    fast: 150,
    normal: 300,
    slow: 500,
  },
  easing: {
    linear: 'linear',
    ease: 'ease',
    easeIn: 'ease-in',
    easeOut: 'ease-out',
    easeInOut: 'ease-in-out',
  },
} as const;

// 浅色主题
export const lightTheme = {
  colors: LightTheme,
  typography: Typography,
  spacing: Spacing,
  borderRadius: BorderRadius,
  shadow: Shadow,
  borderWidth: BorderWidth,
  opacity: Opacity,
  zIndex: ZIndex,
  animation: Animation,
  mode: 'light',
} as const;

// 深色主题
export const darkTheme = {
  colors: DarkTheme,
  typography: Typography,
  spacing: Spacing,
  borderRadius: BorderRadius,
  shadow: Shadow,
  borderWidth: BorderWidth,
  opacity: Opacity,
  zIndex: ZIndex,
  animation: Animation,
  mode: 'dark',
} as const;

// 主题类型定义
export type Theme = typeof lightTheme;
export type ThemeMode = 'light' | 'dark';

// 组件样式预设
export const ComponentStyles = {
  // 按钮样式
  button: {
    primary: {
      backgroundColor: Colors.primary,
      borderRadius: BorderRadius.md,
      paddingHorizontal: Spacing.lg,
      paddingVertical: Spacing.md,
      minHeight: 48,
    },
    secondary: {
      backgroundColor: Colors.backgroundSecondary,
      borderColor: Colors.border,
      borderWidth: BorderWidth.base,
      borderRadius: BorderRadius.md,
      paddingHorizontal: Spacing.lg,
      paddingVertical: Spacing.md,
      minHeight: 48,
    },
    ghost: {
      backgroundColor: 'transparent',
      borderRadius: BorderRadius.md,
      paddingHorizontal: Spacing.lg,
      paddingVertical: Spacing.md,
      minHeight: 48,
    },
  },
  
  // 输入框样式
  input: {
    default: {
      backgroundColor: Colors.surface,
      borderColor: Colors.border,
      borderWidth: BorderWidth.base,
      borderRadius: BorderRadius.md,
      paddingHorizontal: Spacing.md,
      paddingVertical: Spacing.sm,
      minHeight: 48,
      fontSize: FontSize.base,
      fontFamily: FontFamily.system,
    },
    focused: {
      borderColor: Colors.primary,
      borderWidth: BorderWidth.thick,
    },
    error: {
      borderColor: Colors.error,
      borderWidth: BorderWidth.base,
    },
  },
  
  // 卡片样式
  card: {
    default: {
      backgroundColor: Colors.surface,
      borderRadius: BorderRadius.lg,
      padding: Spacing.md,
      ...Shadow.md,
    },
    elevated: {
      backgroundColor: Colors.surface,
      borderRadius: BorderRadius.lg,
      padding: Spacing.lg,
      ...Shadow.lg,
    },
  },
  
  // 容器样式
  container: {
    default: {
      flex: 1,
      backgroundColor: Colors.background,
      paddingHorizontal: Spacing.md,
    },
    centered: {
      flex: 1,
      backgroundColor: Colors.background,
      justifyContent: 'center',
      alignItems: 'center',
      paddingHorizontal: Spacing.md,
    },
  },
} as const;

// 默认主题
export const defaultTheme = lightTheme;

export default defaultTheme;
