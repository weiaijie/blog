// 字体样式定义
import { Platform } from 'react-native';

// 字体家族
export const FontFamily = {
  // 系统默认字体
  system: Platform.select({
    ios: 'System',
    android: 'Roboto',
    default: 'System',
  }),
  
  // 等宽字体
  monospace: Platform.select({
    ios: 'Menlo',
    android: 'monospace',
    default: 'monospace',
  }),
  
  // 自定义字体（需要在项目中添加字体文件）
  // custom: 'YourCustomFont',
} as const;

// 字体大小
export const FontSize = {
  xs: 12,
  sm: 14,
  base: 16,
  lg: 18,
  xl: 20,
  '2xl': 24,
  '3xl': 30,
  '4xl': 36,
  '5xl': 48,
  '6xl': 60,
  '7xl': 72,
  '8xl': 96,
  '9xl': 128,
} as const;

// 字体粗细
export const FontWeight = {
  thin: '100',
  extralight: '200',
  light: '300',
  normal: '400',
  medium: '500',
  semibold: '600',
  bold: '700',
  extrabold: '800',
  black: '900',
} as const;

// 行高
export const LineHeight = {
  none: 1,
  tight: 1.25,
  snug: 1.375,
  normal: 1.5,
  relaxed: 1.625,
  loose: 2,
} as const;

// 字母间距
export const LetterSpacing = {
  tighter: -0.05,
  tight: -0.025,
  normal: 0,
  wide: 0.025,
  wider: 0.05,
  widest: 0.1,
} as const;

// 文本样式预设
export const TextStyles = {
  // 标题样式
  h1: {
    fontFamily: FontFamily.system,
    fontSize: FontSize['4xl'],
    fontWeight: FontWeight.bold,
    lineHeight: LineHeight.tight,
    letterSpacing: LetterSpacing.tight,
  },
  
  h2: {
    fontFamily: FontFamily.system,
    fontSize: FontSize['3xl'],
    fontWeight: FontWeight.bold,
    lineHeight: LineHeight.tight,
    letterSpacing: LetterSpacing.tight,
  },
  
  h3: {
    fontFamily: FontFamily.system,
    fontSize: FontSize['2xl'],
    fontWeight: FontWeight.semibold,
    lineHeight: LineHeight.snug,
    letterSpacing: LetterSpacing.normal,
  },
  
  h4: {
    fontFamily: FontFamily.system,
    fontSize: FontSize.xl,
    fontWeight: FontWeight.semibold,
    lineHeight: LineHeight.snug,
    letterSpacing: LetterSpacing.normal,
  },
  
  h5: {
    fontFamily: FontFamily.system,
    fontSize: FontSize.lg,
    fontWeight: FontWeight.medium,
    lineHeight: LineHeight.normal,
    letterSpacing: LetterSpacing.normal,
  },
  
  h6: {
    fontFamily: FontFamily.system,
    fontSize: FontSize.base,
    fontWeight: FontWeight.medium,
    lineHeight: LineHeight.normal,
    letterSpacing: LetterSpacing.normal,
  },
  
  // 正文样式
  body1: {
    fontFamily: FontFamily.system,
    fontSize: FontSize.base,
    fontWeight: FontWeight.normal,
    lineHeight: LineHeight.normal,
    letterSpacing: LetterSpacing.normal,
  },
  
  body2: {
    fontFamily: FontFamily.system,
    fontSize: FontSize.sm,
    fontWeight: FontWeight.normal,
    lineHeight: LineHeight.normal,
    letterSpacing: LetterSpacing.normal,
  },
  
  // 标签样式
  caption: {
    fontFamily: FontFamily.system,
    fontSize: FontSize.xs,
    fontWeight: FontWeight.normal,
    lineHeight: LineHeight.normal,
    letterSpacing: LetterSpacing.wide,
  },
  
  // 按钮样式
  button: {
    fontFamily: FontFamily.system,
    fontSize: FontSize.base,
    fontWeight: FontWeight.medium,
    lineHeight: LineHeight.none,
    letterSpacing: LetterSpacing.wide,
  },
  
  // 链接样式
  link: {
    fontFamily: FontFamily.system,
    fontSize: FontSize.base,
    fontWeight: FontWeight.normal,
    lineHeight: LineHeight.normal,
    letterSpacing: LetterSpacing.normal,
    textDecorationLine: 'underline',
  },
  
  // 代码样式
  code: {
    fontFamily: FontFamily.monospace,
    fontSize: FontSize.sm,
    fontWeight: FontWeight.normal,
    lineHeight: LineHeight.normal,
    letterSpacing: LetterSpacing.normal,
  },
  
  // 输入框样式
  input: {
    fontFamily: FontFamily.system,
    fontSize: FontSize.base,
    fontWeight: FontWeight.normal,
    lineHeight: LineHeight.normal,
    letterSpacing: LetterSpacing.normal,
  },
  
  // 标签样式
  label: {
    fontFamily: FontFamily.system,
    fontSize: FontSize.sm,
    fontWeight: FontWeight.medium,
    lineHeight: LineHeight.normal,
    letterSpacing: LetterSpacing.normal,
  },
  
  // 错误文本样式
  error: {
    fontFamily: FontFamily.system,
    fontSize: FontSize.xs,
    fontWeight: FontWeight.normal,
    lineHeight: LineHeight.normal,
    letterSpacing: LetterSpacing.normal,
  },
  
  // 帮助文本样式
  helper: {
    fontFamily: FontFamily.system,
    fontSize: FontSize.xs,
    fontWeight: FontWeight.normal,
    lineHeight: LineHeight.normal,
    letterSpacing: LetterSpacing.normal,
  },
} as const;

// 文本对齐
export const TextAlign = {
  left: 'left',
  center: 'center',
  right: 'right',
  justify: 'justify',
} as const;

// 文本装饰
export const TextDecoration = {
  none: 'none',
  underline: 'underline',
  lineThrough: 'line-through',
} as const;

// 文本变换
export const TextTransform = {
  none: 'none',
  uppercase: 'uppercase',
  lowercase: 'lowercase',
  capitalize: 'capitalize',
} as const;

// 导出默认字体样式
export const Typography = TextStyles;

export default Typography;
