# vue-pos

## Project setup
```
npm install
```

### Compiles and hot-reloads for development
```
npm run serve
```

### Compiles and minifies for production
```
npm run build
```

### Customize configuration
See [Configuration Reference](https://cli.vuejs.org/config/).



我来分析一下这个前端项目的打包和调试方式。
根据分析,这是一个基于 **uni-app** 框架开发的前端项目,可以打包成安卓 APP。以下是详细分析:

## 📱 项目概况

**项目名称**: vue-pos (vue-store-big-phone)  
**技术栈**: uni-app + Vue 2 + Vuex  
**支持平台**: H5、App(Android/iOS)、小程序、快应用等多端

## 🔧 打包成安卓 APP

### 1. **打包构建模式**

项目支持三种 APP 打包模式:

#### 模式一:H5 模式打包
```bash
npm run build
# 或
npm run serve  # 本地调试
```
- 端口: 9534
- 生成 H5 网页版本

#### 模式二:WebView 混合模式 (推荐用于 APP)
```bash
# 本地开发环境(方便本地调试)
npm run build:local-fb-webview   # 本地 FB 环境
npm run build:local-qyh-webview  # 本地 QYH 环境

# 测试环境
npm run build:dev-webview        # 开发环境

# UAT 环境
npm run build:uat-webview        # UAT 测试环境

# 生产环境
npm run build:webview            # 正式生产环境
npm run build:webview-ey100      # EY100 定制版本
```

#### 模式三:原生 App-Plus 模式
```bash
# 本地环境
npm run build:local-fb-app-plus   # 本地 FB 环境
npm run build:local-qyh-app-plus  # 本地 QYH 环境

# 测试环境
npm run build:dev-app-plus        # 开发环境

# UAT 环境
npm run build:uat-app-plus        # UAT 环境

# 生产环境
npm run build:app-plus            # 生产环境
npm run build:app-plus-ey100      # EY100 定制版
```

### 2. **打包后的处理**

执行打包命令后,会在项目根目录生成 `dist/build/app-plus` 目录,需要:

1. **使用 HBuilderX**:
   - 打开 HBuilderX IDE
   - 导入 `dist/build/app-plus` 目录
   - 发行 → 原生 App-云打包 → 配置证书和签名
   - 生成 APK 文件

2. **或使用 Android Studio** (需要配置原生插件):
   - 在 `frontend/android-pos` 目录有对应的 Android 原生项目
   - 将打包产物集成到 Android 项目中

## 🚀 启动调试

### 1. **H5 本地调试** (最简单)
```bash
# 安装依赖
npm install

# 启动 H5 开发服务器
npm run serve
# 或
npm run serve:webview  # WebView 模式调试
```
访问: http://localhost:9534

### 2. **App 真机调试**

#### 方式一:HBuilderX 真机调试
1. 安装 HBuilderX
2. 打开项目
3. 连接安卓手机(开启 USB 调试)
4. 运行 → 运行到手机或模拟器 → 选择设备

#### 方式二:离线打包调试
```bash
# 1. 构建 App 资源
npm run build:dev-app-plus

# 2. 使用 Android Studio 打开 frontend/android-pos 项目
# 3. 将构建产物复制到 Android 项目
# 4. 编译安装到手机
```

### 3. **不同环境调试**

```bash
# 本地后端联调(指向 192.168.x.x)
npm run build:local-fb-app-plus  # NODE_ENV=localhostFB

# 连接测试环境 API
npm run build:dev-app-plus       # NODE_ENV=development

# 连接 UAT 环境
npm run build:uat-app-plus       # NODE_ENV=uat
```

## 📂 关键配置文件

| 文件 | 作用 |
|------|------|
| [src/manifest.json](file:///Users/saber/Desktop/cjkj/CJKJ.Product/frontend/vue-store-big-phone/src/manifest.json) | uni-app 应用配置(应用ID、权限、启动页等) |
| [src/pages.webview.json](file:///Users/saber/Desktop/cjkj/CJKJ.Product/frontend/vue-store-big-phone/src/pages.webview.json) | WebView 模式的页面路由配置 |
| [src/config.js](file:///Users/saber/Desktop/cjkj/CJKJ.Product/frontend/vue-store-big-phone/src/config.js) | 环境配置(API 地址、图片 CDN 等) |
| [app.build.js](file:///Users/saber/Desktop/cjkj/CJKJ.Product/frontend/vue-store-big-phone/app.build.js) | 构建脚本(根据 build 参数切换 pages 配置) |
| [frontend/android-pos/](file:///Users/saber/Desktop/cjkj/CJKJ.Product/frontend/android-pos) | Android 原生项目(包含原生插件) |

## 🔑 特殊功能

1. **多环境配置**: 支持本地、开发、UAT、生产、EY100 定制版
2. **原生插件**: 集成了 POS 机相关原生插件(在 `android-pos/uniplugin_cjkj_pos`)
3. **应用升级**: 内置 `uni-upgrade-center-app` 升级模块
4. **RFID 模式**: 支持 RFID 设备专用打包(`build:rfid`)

## 💡 推荐调试流程

```bash
# 1. 安装依赖
npm install

# 2. H5 模式快速预览
npm run serve

# 3. 打包 WebView 版本(用于 APP)
npm run build:dev-webview

# 4. 使用 HBuilderX 打包 APK 或真机调试
```

需要我帮你执行某个具体的打包或调试命令吗?