# React Native学习测试应用

这是一个用于学习和测试React Native各种特性和功能的移动应用项目。

## 项目概述

- **项目名称**: RN学习测试应用
- **技术栈**: React Native, TypeScript, Redux Toolkit
- **开发环境**: Windows
- **目标平台**: iOS, Android

## 功能特性

### 已实现功能
- ✅ 项目基础架构搭建
- ✅ TypeScript配置
- ✅ ESLint和Prettier代码规范
- ✅ 文件夹结构组织
- ✅ 基础工具函数
- ✅ 主题系统
- ✅ 存储工具

### 计划实现功能
- 🔄 用户认证系统
- 🔄 导航系统
- 🔄 状态管理
- 🔄 UI组件库
- 🔄 网络请求
- 🔄 设备功能集成
- 🔄 测试框架

## 项目结构

```
app/
├── src/                    # 源代码目录
│   ├── components/         # 通用组件
│   ├── screens/           # 页面组件
│   ├── navigation/        # 导航配置
│   ├── services/          # API服务
│   ├── store/             # 状态管理
│   ├── utils/             # 工具函数
│   ├── hooks/             # 自定义Hooks
│   ├── types/             # TypeScript类型
│   ├── assets/            # 静态资源
│   └── styles/            # 样式文件
├── __tests__/             # 测试文件
├── android/               # Android原生代码
├── ios/                   # iOS原生代码
└── package.json           # 项目依赖
```

## 开发环境要求

### 必需软件
- Node.js 18.0+
- npm 8.0+
- React Native CLI
- Android Studio (Android开发)
- Xcode (iOS开发，仅macOS)

### 推荐工具
- VS Code
- React Native Debugger
- Flipper
- Reactotron

## 快速开始

### 1. 安装依赖
```bash
npm install
```

### 2. iOS开发 (仅macOS)
```bash
cd ios && pod install && cd ..
npm run ios
```

### 3. Android开发
```bash
npm run android
```

### 4. 启动Metro服务器
```bash
npm start
```

## 可用脚本

- `npm start` - 启动Metro服务器
- `npm run android` - 运行Android应用
- `npm run ios` - 运行iOS应用
- `npm test` - 运行测试
- `npm run lint` - 代码检查
- `npm run lint:fix` - 自动修复代码问题
- `npm run format` - 格式化代码
- `npm run type-check` - TypeScript类型检查

## 代码规范

### 命名规范
- 组件文件使用PascalCase: `LoginScreen.tsx`
- 工具文件使用camelCase: `helpers.ts`
- 常量使用UPPER_SNAKE_CASE: `API_BASE_URL`

### 文件组织
- 每个组件一个文件
- 相关文件放在同一目录
- 使用index.ts文件导出

### 提交规范
- feat: 新功能
- fix: 修复bug
- docs: 文档更新
- style: 代码格式
- refactor: 重构
- test: 测试相关
- chore: 构建过程或辅助工具的变动

## 技术栈详情

### 核心技术
- **React Native**: 跨平台移动应用框架
- **TypeScript**: 类型安全的JavaScript
- **Redux Toolkit**: 状态管理
- **React Navigation**: 导航库

### UI和样式
- **React Native Elements**: UI组件库
- **Styled Components**: CSS-in-JS样式
- **React Native Vector Icons**: 图标库

### 开发工具
- **ESLint**: 代码检查
- **Prettier**: 代码格式化
- **Jest**: 测试框架
- **Flipper**: 调试工具

## 学习资源

### 官方文档
- [React Native官方文档](https://reactnative.dev/)
- [TypeScript官方文档](https://www.typescriptlang.org/)
- [Redux Toolkit文档](https://redux-toolkit.js.org/)

### 推荐教程
- React Native中文网
- 掘金React Native专栏
- YouTube React Native教程

## 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 许可证

MIT License

## 联系方式

如有问题或建议，请通过以下方式联系：
- 邮箱: developer@example.com
- GitHub Issues

---

**注意**: 这是一个学习项目，仅用于教育和测试目的。
