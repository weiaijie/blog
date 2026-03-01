/**
 * 导航守卫入口文件
 * 
 * 导出所有导航守卫和相关工具
 */

export { 
  createAuthGuard, 
  defaultAuthGuard, 
  adminGuard, 
  vipGuard 
} from './AuthGuard';

// 可以在这里添加更多守卫
// export { default as RoleGuard } from './RoleGuard';
// export { default as PermissionGuard } from './PermissionGuard';
