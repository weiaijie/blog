# NestApp - NestJS 后端学习项目

## 📋 项目概述

这是一个基于 NestJS 框架构建的后端 API 学习项目。NestJS 是一个用于构建高效、可扩展的 Node.js 服务器端应用程序的渐进式框架，采用 TypeScript 编写，结合了 OOP（面向对象编程）、FP（函数式编程）和 FRP（函数响应式编程）的元素。

## 🚀 技术栈

### 核心框架
- **NestJS 10.0.0** - 渐进式 Node.js 框架
- **TypeScript 5.2.2** - 强类型 JavaScript 超集
- **Node.js** - JavaScript 运行时环境
- **Express** - 底层 HTTP 服务器框架

### 开发工具链
- **pnpm** - 高效的包管理器
- **ESLint** - 代码质量检查工具
- **Prettier** - 代码格式化工具
- **Jest** - 测试框架
- **Supertest** - HTTP 断言测试
- **ts-node** - TypeScript 直接执行器

### 核心依赖
- **@nestjs/common** - NestJS 核心模块
- **@nestjs/core** - NestJS 核心功能
- **@nestjs/platform-express** - Express 平台适配器
- **reflect-metadata** - 装饰器元数据支持
- **rxjs** - 响应式编程库

## 📁 项目结构

```
nestapp/
├── src/                          # 源代码目录
│   ├── app.controller.ts         # 应用控制器
│   ├── app.controller.spec.ts    # 控制器测试文件
│   ├── app.module.ts             # 根模块
│   ├── app.service.ts            # 应用服务
│   └── main.ts                   # 应用入口文件
├── test/                         # E2E 测试目录
│   ├── app.e2e-spec.ts          # 端到端测试
│   └── jest-e2e.json            # E2E 测试配置
├── dist/                         # 编译输出目录
├── node_modules/                 # 依赖包目录
├── nest-cli.json                 # NestJS CLI 配置
├── package.json                  # 项目配置和依赖
├── pnpm-lock.yaml               # pnpm 锁定文件
├── tsconfig.json                # TypeScript 配置
├── tsconfig.build.json          # 构建 TypeScript 配置
└── README.md                    # 项目说明文档
```

## 🛠️ 开发环境配置

### 环境要求
- **Node.js** >= 16.0.0
- **pnpm** >= 7.0.0 (推荐) 或 npm >= 8.0.0
- **TypeScript** >= 4.7.0

### 安装依赖
```bash
cd nestapp
pnpm install
```

## 🎯 可用脚本命令

### 开发相关
```bash
# 开发模式启动 (监听文件变化)
pnpm run start:dev

# 普通启动
pnpm run start

# 调试模式启动
pnpm run start:debug

# 生产模式启动
pnpm run start:prod
```

### 构建相关
```bash
# 编译 TypeScript 代码
pnpm run build

# 代码格式化
pnpm run format

# 代码检查和修复
pnpm run lint
```

### 测试相关
```bash
# 单元测试
pnpm run test

# 监听模式测试
pnpm run test:watch

# 测试覆盖率
pnpm run test:cov

# E2E 测试
pnpm run test:e2e

# 调试测试
pnpm run test:debug
```

## 🏗️ 架构设计

### NestJS 核心概念

#### 1. 模块 (Modules)
- **根模块 (AppModule)**: 应用程序的入口点
- **功能模块**: 按功能划分的业务模块
- **共享模块**: 可复用的公共模块

#### 2. 控制器 (Controllers)
- 处理 HTTP 请求
- 定义路由和请求方法
- 调用服务层处理业务逻辑

#### 3. 服务 (Services/Providers)
- 业务逻辑处理
- 数据访问和操作
- 可注入的依赖

#### 4. 装饰器 (Decorators)
- `@Module()` - 定义模块
- `@Controller()` - 定义控制器
- `@Injectable()` - 定义可注入服务
- `@Get()`, `@Post()` 等 - 定义路由

### 依赖注入 (DI)
NestJS 使用强大的依赖注入系统，实现：
- 松耦合的代码结构
- 易于测试和维护
- 自动的依赖管理

## 🎨 功能特性

### 当前功能
- ✅ 基础 HTTP 服务器
- ✅ RESTful API 结构
- ✅ TypeScript 强类型支持
- ✅ 依赖注入系统
- ✅ 单元测试和 E2E 测试
- ✅ 代码质量检查
- ✅ 热重载开发模式

### 可扩展功能
- 🔄 数据库集成 (TypeORM/Prisma)
- 🔄 身份验证和授权 (JWT/Passport)
- 🔄 API 文档 (Swagger)
- 🔄 配置管理 (@nestjs/config)
- 🔄 缓存系统 (Redis)
- 🔄 消息队列 (Bull/RabbitMQ)
- 🔄 文件上传处理
- 🔄 WebSocket 支持
- 🔄 微服务架构

## 📚 学习路径建议

### 初级阶段
1. **NestJS 基础概念**
   - 理解装饰器和依赖注入
   - 掌握模块、控制器、服务的概念
   - 学习路由和 HTTP 方法处理

2. **实践项目**
   - 创建简单的 CRUD API
   - 实现数据验证和错误处理
   - 编写基础的单元测试

### 中级阶段
1. **数据库集成**
   - 学习 TypeORM 或 Prisma
   - 实现数据模型和关系
   - 掌握数据库迁移

2. **身份验证**
   - 实现 JWT 认证
   - 添加角色和权限控制
   - 学习 Passport 策略

### 高级阶段
1. **高级特性**
   - 微服务架构设计
   - GraphQL API 开发
   - 性能优化和监控

2. **生产部署**
   - Docker 容器化
   - CI/CD 流水线
   - 云平台部署

## 🔧 开发最佳实践

### 代码组织
```typescript
// 推荐的文件命名约定
user.controller.ts    // 控制器
user.service.ts       // 服务
user.module.ts        // 模块
user.entity.ts        // 实体
user.dto.ts          // 数据传输对象
user.interface.ts     // 接口定义
```

### 错误处理
```typescript
import { HttpException, HttpStatus } from '@nestjs/common';

throw new HttpException('用户未找到', HttpStatus.NOT_FOUND);
```

### 数据验证
```typescript
import { IsString, IsEmail, IsNotEmpty } from 'class-validator';

export class CreateUserDto {
  @IsString()
  @IsNotEmpty()
  name: string;

  @IsEmail()
  email: string;
}
```

## 🌐 API 文档

### 默认端点
- **GET /** - 根路径，返回 "Hello World!"
- **健康检查** - 可添加 `/health` 端点
- **API 版本** - 建议使用 `/api/v1` 前缀

### Swagger 集成 (可选)
```bash
pnpm add @nestjs/swagger swagger-ui-express
```

访问 API 文档：http://localhost:3000/api

## 🚀 部署选项

### 传统部署
1. **VPS/云服务器**
   - 直接部署到 Linux 服务器
   - 使用 PM2 进程管理
   - Nginx 反向代理

### 容器化部署
2. **Docker**
   - 创建 Dockerfile
   - 使用 docker-compose
   - 容器编排部署

### 云平台部署
3. **云服务**
   - **Heroku** - 简单快速部署
   - **AWS/阿里云** - 企业级云服务
   - **Vercel** - Serverless 部署

## 📖 学习资源

### 官方文档
- [NestJS 官方文档](https://nestjs.com/)
- [NestJS 中文文档](https://nestjs.bootcss.com/)

### 推荐教程
- [TypeScript 官方文档](https://www.typescriptlang.org/)
- [Node.js 最佳实践](https://github.com/goldbergyoni/nodebestpractices)

### 社区资源
- [NestJS GitHub](https://github.com/nestjs/nest)
- [Awesome NestJS](https://github.com/nestjs/awesome-nestjs)

## 🧪 测试策略

### 单元测试
- 测试服务层业务逻辑
- 模拟外部依赖
- 保持高测试覆盖率

### 集成测试
- 测试模块间交互
- 数据库集成测试
- API 端点测试

### E2E 测试
- 完整的用户场景测试
- 真实环境模拟
- 关键业务流程验证

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 遵循代码规范 (`pnpm run lint`)
4. 添加测试用例
5. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
6. 推送到分支 (`git push origin feature/AmazingFeature`)
7. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🔍 项目扩展示例

### 添加新的模块
```bash
# 使用 NestJS CLI 生成新模块
nest generate module users
nest generate controller users
nest generate service users
```

### 数据库集成示例
```typescript
// user.entity.ts
import { Entity, Column, PrimaryGeneratedColumn } from 'typeorm';

@Entity()
export class User {
  @PrimaryGeneratedColumn()
  id: number;

  @Column()
  name: string;

  @Column()
  email: string;
}
```

### 环境配置
```typescript
// app.module.ts
import { ConfigModule } from '@nestjs/config';

@Module({
  imports: [
    ConfigModule.forRoot({
      isGlobal: true,
    }),
  ],
})
export class AppModule {}
```

## 🐛 常见问题解决

### 端口冲突
如果 3000 端口被占用，可以修改 `main.ts`:
```typescript
await app.listen(process.env.PORT || 3001);
```

### TypeScript 编译错误
确保 `tsconfig.json` 配置正确：
```json
{
  "compilerOptions": {
    "experimentalDecorators": true,
    "emitDecoratorMetadata": true
  }
}
```

### 依赖注入问题
确保服务类使用 `@Injectable()` 装饰器：
```typescript
import { Injectable } from '@nestjs/common';

@Injectable()
export class AppService {
  // 服务实现
}
```

## 📊 性能监控

### 添加日志记录
```typescript
import { Logger } from '@nestjs/common';

export class AppService {
  private readonly logger = new Logger(AppService.name);

  getHello(): string {
    this.logger.log('Hello World 请求被调用');
    return 'Hello World!';
  }
}
```

### 健康检查端点
```bash
pnpm add @nestjs/terminus
```

## 🔐 安全最佳实践

### 基础安全配置
```bash
# 安装安全相关包
pnpm add helmet compression
pnpm add @types/compression --save-dev
```

### CORS 配置
```typescript
// main.ts
app.enableCors({
  origin: ['http://localhost:3000'],
  credentials: true,
});
```

---

**Happy Coding with NestJS! 🎉**
