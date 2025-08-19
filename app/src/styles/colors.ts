// 颜色定义文件

// 基础颜色
export const BaseColors = {
  // 主色调
  primary: '#007AFF',
  primaryDark: '#0056CC',
  primaryLight: '#4DA3FF',
  
  // 辅助色
  secondary: '#5856D6',
  secondaryDark: '#3F3E9F',
  secondaryLight: '#7B7AE8',
  
  // 成功色
  success: '#34C759',
  successDark: '#248A3D',
  successLight: '#5DD87A',
  
  // 警告色
  warning: '#FF9500',
  warningDark: '#CC7700',
  warningLight: '#FFB340',
  
  // 错误色
  error: '#FF3B30',
  errorDark: '#CC2E25',
  errorLight: '#FF6B62',
  
  // 信息色
  info: '#5AC8FA',
  infoDark: '#32A0C8',
  infoLight: '#7DD3FB',
  
  // 中性色
  white: '#FFFFFF',
  black: '#000000',
  transparent: 'transparent',
} as const;

// 灰度色阶
export const GrayColors = {
  gray50: '#F9FAFB',
  gray100: '#F3F4F6',
  gray200: '#E5E7EB',
  gray300: '#D1D5DB',
  gray400: '#9CA3AF',
  gray500: '#6B7280',
  gray600: '#4B5563',
  gray700: '#374151',
  gray800: '#1F2937',
  gray900: '#111827',
} as const;

// 浅色主题颜色
export const LightTheme = {
  // 背景色
  background: BaseColors.white,
  backgroundSecondary: GrayColors.gray50,
  backgroundTertiary: GrayColors.gray100,
  
  // 表面色
  surface: BaseColors.white,
  surfaceSecondary: GrayColors.gray50,
  
  // 文本色
  text: GrayColors.gray900,
  textSecondary: GrayColors.gray600,
  textTertiary: GrayColors.gray400,
  textInverse: BaseColors.white,
  
  // 边框色
  border: GrayColors.gray200,
  borderSecondary: GrayColors.gray300,
  
  // 分割线
  divider: GrayColors.gray200,
  
  // 阴影色
  shadow: 'rgba(0, 0, 0, 0.1)',
  shadowDark: 'rgba(0, 0, 0, 0.2)',
  
  // 覆盖层
  overlay: 'rgba(0, 0, 0, 0.5)',
  overlayLight: 'rgba(0, 0, 0, 0.3)',
  
  // 状态色
  ...BaseColors,
} as const;

// 深色主题颜色
export const DarkTheme = {
  // 背景色
  background: GrayColors.gray900,
  backgroundSecondary: GrayColors.gray800,
  backgroundTertiary: GrayColors.gray700,
  
  // 表面色
  surface: GrayColors.gray800,
  surfaceSecondary: GrayColors.gray700,
  
  // 文本色
  text: BaseColors.white,
  textSecondary: GrayColors.gray300,
  textTertiary: GrayColors.gray400,
  textInverse: GrayColors.gray900,
  
  // 边框色
  border: GrayColors.gray600,
  borderSecondary: GrayColors.gray500,
  
  // 分割线
  divider: GrayColors.gray600,
  
  // 阴影色
  shadow: 'rgba(0, 0, 0, 0.3)',
  shadowDark: 'rgba(0, 0, 0, 0.5)',
  
  // 覆盖层
  overlay: 'rgba(0, 0, 0, 0.7)',
  overlayLight: 'rgba(0, 0, 0, 0.5)',
  
  // 状态色
  ...BaseColors,
} as const;

// 语义化颜色
export const SemanticColors = {
  // 链接色
  link: BaseColors.primary,
  linkHover: BaseColors.primaryDark,
  
  // 禁用色
  disabled: GrayColors.gray400,
  disabledBackground: GrayColors.gray100,
  
  // 选中色
  selected: BaseColors.primary,
  selectedBackground: BaseColors.primaryLight,
  
  // 焦点色
  focus: BaseColors.primary,
  focusBackground: 'rgba(0, 122, 255, 0.1)',
  
  // 悬停色
  hover: GrayColors.gray100,
  hoverDark: GrayColors.gray700,
} as const;

// 渐变色
export const GradientColors = {
  primary: [BaseColors.primary, BaseColors.primaryDark],
  secondary: [BaseColors.secondary, BaseColors.secondaryDark],
  success: [BaseColors.success, BaseColors.successDark],
  warning: [BaseColors.warning, BaseColors.warningDark],
  error: [BaseColors.error, BaseColors.errorDark],
  info: [BaseColors.info, BaseColors.infoDark],
  sunset: ['#FF6B6B', '#FF8E53', '#FF6B9D'],
  ocean: ['#667eea', '#764ba2'],
  forest: ['#134E5E', '#71B280'],
} as const;

// 导出默认颜色（浅色主题）
export const Colors = LightTheme;

export default Colors;
