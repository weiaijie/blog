# React Navigation 导航系统完整指南

## 📋 目录

1. [项目概述](#项目概述)
2. [安装步骤](#安装步骤)
3. [配置说明](#配置说明)
4. [功能特性](#功能特性)
5. [使用示例](#使用示例)
6. [文件说明](#文件说明)
7. [常见问题](#常见问题)

---

## 📊 项目概述

### 已完成的工作

#### ✅ 新建文件（5个）：

1. **`src/navigation/navigation.types.ts`** - TypeScript类型定义
2. **`src/navigation/linking.ts`** - URL路由配置
3. **`src/navigation/RNAuthNavigator.tsx`** - 认证导航器（登录/注册）
4. **`src/navigation/RNMainNavigator.tsx`** - 主应用Tab导航器
5. **`src/navigation/RNAppNavigator.tsx`** - 根导航器

#### 🔧 修改文件（3个）：

1. **`src/App.tsx`** - 使用新的导航系统
2. **`src/screens/auth/LoginScreen.tsx`** - 支持React Navigation
3. **`src/screens/auth/RegisterScreen.tsx`** - 支持React Navigation

### 导航架构

```
App
└── Redux Provider
    └── ThemeProvider (主题)
        └── AuthProvider (认证)
            └── NavigationContainer (React Navigation)
                └── RNAppNavigator (根导航)
                    ├── Auth Stack (未登录)
                    │   ├── LoginScreen (登录)
                    │   └── RegisterScreen (注册)
                    └── Main Stack (已登录)
                        └── Tab Navigator (底部Tab)
                            ├── HomeScreen (首页)
                            ├── TodoScreen (待办)
                            ├── ProfileScreen (个人)
                            └── SettingsScreen (设置)
```

---

## 📦 安装步骤

### 第一步：安装依赖包

在终端运行以下命令：

```bash
npm install @react-navigation/native @react-navigation/native-stack @react-navigation/bottom-tabs react-native-screens react-native-safe-area-context
```

### 第二步：配置Android

编辑 `android/app/src/main/java/com/rnlearningapp/MainActivity.java`：

在文件顶部添加：
```java
import android.os.Bundle;
```

在MainActivity类中添加方法：
```java
@Override
protected void onCreate(Bundle savedInstanceState) {
  super.onCreate(null);
}
```

### 第三步：配置iOS（如果需要）

```bash
cd ios && pod install && cd ..
```

在 `ios/rnlearningapp/AppDelegate.mm` 中添加：
```objc
#import <React/RCTLinkingManager.h>

- (BOOL)application:(UIApplication *)application
   openURL:(NSURL *)url
   options:(NSDictionary<UIApplicationOpenURLOptionsKey,id> *)options
{
  return [RCTLinkingManager application:application openURL:url options:options];
}
```

### 第四步：清理缓存并运行

```bash
# 清理缓存
npm start -- --reset-cache

# 运行Web端
npm run web

# 运行Android
npm run android

# 运行iOS
npm run ios
```

---

## 🎯 功能特性

### 移动端功能

- ✅ **原生页面栈** - 完整的页面历史管理
- ✅ **原生Tab导航** - 底部标签栏切换
- ✅ **原生动画** - 滑动、淡入淡出等动画效果
- ✅ **手势支持** - iOS滑动返回、Android返回键
- ✅ **深度链接** - 支持外部链接打开应用
- ✅ **类型安全** - 完整的TypeScript类型支持

### Web端功能

- ✅ **URL路由** - 每个页面有独立URL
  - `/` - 首页
  - `/todo` - 待办页面
  - `/profile` - 个人页面
  - `/settings` - 设置页面
  - `/login` - 登录页面
  - `/register` - 注册页面
- ✅ **浏览器导航** - 前进/后退按钮正常工作
- ✅ **直接访问** - 可以直接访问任何URL
- ✅ **分享链接** - 可以分享特定页面链接
- ✅ **页面标题** - 自动更新浏览器标题
- ✅ **刷新保持** - 刷新页面保持当前位置

---

## 💡 使用示例

### 基础导航

```typescript
import { useNavigation } from '@react-navigation/native';

function MyComponent() {
  const navigation = useNavigation();

  return (
    <View>
      <Button 
        title="去个人页面" 
        onPress={() => navigation.navigate('Profile')} 
      />
      <Button 
        title="返回" 
        onPress={() => navigation.goBack()} 
      />
    </View>
  );
}
```

### 带参数导航

```typescript
// 导航并传递参数
navigation.navigate('TodoDetail', {
  id: '123',
  title: '学习React Navigation',
});

// 接收参数
import { useRoute } from '@react-navigation/native';

function TodoDetailScreen() {
  const route = useRoute();
  const { id, title } = route.params;
  
  return (
    <View>
      <Text>ID: {id}</Text>
      <Text>标题: {title}</Text>
    </View>
  );
}
```

### 获取当前路由

```typescript
import { useRoute } from '@react-navigation/native';

function MyComponent() {
  const route = useRoute();
  
  console.log('当前页面:', route.name);
  console.log('参数:', route.params);
}
```

---

## 📁 文件说明

### 1. navigation.types.ts - 类型定义

定义了所有导航器的类型，提供完整的TypeScript支持：

- `RootStackParamList` - 根导航器参数
- `AuthStackParamList` - 认证导航器参数
- `MainTabParamList` - Tab导航器参数

### 2. linking.ts - URL路由配置

配置Web端URL路由和移动端深度链接：

- URL前缀配置（localhost、生产域名）
- 路由映射（页面名称 → URL路径）
- URL监听和解析

### 3. RNAuthNavigator.tsx - 认证导航器

管理登录和注册页面的Stack导航：

- 登录页面
- 注册页面
- 页面切换动画

### 4. RNMainNavigator.tsx - 主应用导航器

管理主应用的Tab导航：

- 首页Tab
- 待办Tab
- 个人Tab
- 设置Tab
- Tab图标和样式

### 5. RNAppNavigator.tsx - 根导航器

应用的主导航器，根据登录状态切换：

- 未登录 → 显示认证导航器
- 已登录 → 显示主应用导航器
- 主题配置
- Linking配置

---

## 🔧 自定义配置

### 修改Tab图标

编辑 `src/navigation/RNMainNavigator.tsx`：

```typescript
<Tab.Screen
  name="Home"
  component={HomeScreen}
  options={{
    tabBarIcon: ({ focused, color }) => (
      <Text style={{ fontSize: focused ? 24 : 20 }}>
        🏠
      </Text>
    ),
  }}
/>
```

### 修改页面标题

```typescript
<Stack.Screen
  name="Login"
  component={LoginScreen}
  options={{
    title: '用户登录',
    headerShown: true,
  }}
/>
```

### 修改导航动画

```typescript
<Stack.Navigator
  screenOptions={{
    animation: 'slide_from_right', // 或 'fade', 'slide_from_bottom'
  }}
>
```

### 添加Tab徽章

```typescript
<Tab.Screen
  name="Todo"
  component={TodoScreen}
  options={{
    tabBarBadge: 3, // 显示数字徽章
  }}
/>
```

---

## 🐛 常见问题

### 问题1：找不到@react-navigation模块

**原因：** 依赖未安装

**解决：**
```bash
npm install
npm start -- --reset-cache
```

### 问题2：Android构建失败

**解决：**
```bash
cd android
./gradlew clean
cd ..
npm run android
```

### 问题3：iOS构建失败

**解决：**
```bash
cd ios
pod install
cd ..
npm run ios
```

### 问题4：Web端URL不变化

**检查：**
- 确保使用的是RNAppNavigator
- 检查linking配置是否正确
- 查看浏览器控制台错误

### 问题5：页面切换没有动画

**原因：** 可能是在Web端

**说明：** Web端动画效果不如移动端，这是正常的

---

## ✅ 测试清单

### 移动端测试

- [ ] 应用启动正常
- [ ] 登录页面显示
- [ ] 可以切换到注册页面
- [ ] 登录成功进入主应用
- [ ] Tab导航切换正常
- [ ] 页面切换有动画
- [ ] Android返回键正常
- [ ] iOS滑动返回正常

### Web端测试

- [ ] 浏览器打开 http://localhost:3000
- [ ] URL显示为 `/login`
- [ ] 登录后URL变为 `/`
- [ ] 点击Tab时URL改变
- [ ] 浏览器前进/后退正常
- [ ] 直接访问 `/profile` 可以打开
- [ ] 刷新页面保持位置

---

## 🗑️ 可以删除的旧文件

安装测试通过后，可以删除：

- `src/navigation/components/SimpleAppNavigator.tsx`
- `src/navigation/components/WebAppNavigator.tsx`
- `src/navigation/components/MainAppNavigator.tsx`
- `src/navigation/components/AuthNavigator.tsx`
- `src/navigation/Router.ts`
- `src/navigation/NavigationContext.tsx`
- `src/navigation/guards/`
- `src/navigation/types.ts`

---

## 📚 参考资源

- [React Navigation官方文档](https://reactnavigation.org/)
- [TypeScript支持](https://reactnavigation.org/docs/typescript)
- [Linking配置](https://reactnavigation.org/docs/configuring-links)
- [深度链接](https://reactnavigation.org/docs/deep-linking)

---

## 🎉 总结

现在您拥有：

- ✅ 功能完整的导航系统
- ✅ 移动端和Web端都支持
- ✅ 类型安全的TypeScript
- ✅ 原生动画和手势
- ✅ 灵活的URL路由
- ✅ 易于扩展维护

准备开始安装了吗？

