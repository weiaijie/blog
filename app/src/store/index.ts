/**
 * Redux Store 配置
 *
 * 这是应用的全局状态管理配置文件，提供：
 *
 * 主要功能：
 * 1. Redux Store配置 - 使用Redux Toolkit简化配置
 * 2. Reducer组合 - 将各个功能模块的reducer组合
 * 3. 中间件配置 - 配置序列化检查等中间件
 * 4. 类型定义 - 导出TypeScript类型定义
 *
 * 架构说明：
 * - 使用Redux Toolkit的configureStore简化配置
 * - 支持开发工具和时间旅行调试
 * - 内置了常用中间件（thunk、序列化检查等）
 * - 提供完整的TypeScript类型支持
 *
 * 注意：目前为简化版本，主要用于学习目的
 * 在实际项目中可以根据需要添加更多的reducer和中间件
 */

import { configureStore } from '@reduxjs/toolkit';

/**
 * 创建Redux Store
 *
 * 配置说明：
 * - reducer: 组合所有功能模块的reducer
 * - middleware: 配置中间件，包括序列化检查
 * - devTools: 自动启用Redux DevTools（仅开发环境）
 *
 * 注意：目前为简化版本，主要用于学习目的
 * 实际的状态管理通过Context和自定义Hooks实现
 */
export const store = configureStore({
  reducer: {
    // 暂时使用一个简单的reducer来避免空reducer错误
    app: (state = { initialized: true }, action) => state,
    // 可以在这里添加更多的reducer
    // auth: authReducer,  // 用户认证状态管理（目前使用自定义Hook）
    // theme: themeReducer,  // 主题状态管理（目前使用Context）
    // todos: todosReducer,  // 待办事项状态管理（目前使用本地状态）
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        // 忽略某些action的序列化检查
        // 这对于处理Date对象或其他非序列化数据很有用
        ignoredActions: ['persist/PERSIST'],
      },
    }),
});

/**
 * 根状态类型定义
 * 从store中推断出完整的状态类型
 *
 * 使用方式：
 * const state: RootState = useSelector(state => state);
 */
export type RootState = ReturnType<typeof store.getState>;

/**
 * Dispatch类型定义
 * 包含所有中间件增强的dispatch类型
 *
 * 使用方式：
 * const dispatch: AppDispatch = useDispatch();
 */
export type AppDispatch = typeof store.dispatch;

// ==================== 导出认证相关功能 ====================

/**
 * 导出认证Hook和类型
 * 虽然我们使用了简化的Redux store，但认证功能通过自定义Hook实现
 */
export { default as useAuth } from './slices/authSlice';
export type { User, AuthState } from './slices/authSlice';
