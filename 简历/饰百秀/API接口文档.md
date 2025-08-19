# Special 项目 API 接口文档

## 接口概览

### 基础信息
- **基础URL**: `http://home.special-china.com/special/public/index.php`
- **中间层URL**: `http://localhost:8669`
- **请求格式**: `application/x-www-form-urlencoded`
- **响应格式**: `JSON`

### 通用响应格式
```json
{
  "code": 1,           // 状态码：1-成功，-1-失败，1001-未登录
  "msg": "success",    // 消息
  "data": {}          // 数据
}
```

## 1. 用户认证模块

### 1.1 飞书登录
- **接口**: `POST /index/login/feishu_login`
- **描述**: 通过飞书进行用户登录
- **参数**:
  ```json
  {
    "code": "string",      // 飞书授权码
    "state": "string"      // 状态参数
  }
  ```
- **响应**:
  ```json
  {
    "code": 1,
    "msg": "登录成功",
    "data": {
      "token": "string",
      "user_info": {
        "id": 1,
        "name": "用户名",
        "role": "角色"
      }
    }
  }
  ```

### 1.2 获取用户信息
- **接口**: `GET /auth/info`
- **描述**: 获取当前登录用户信息
- **参数**: 
  ```json
  {
    "token": "string"    // 用户Token
  }
  ```

### 1.3 验证Token
- **接口**: `GET /index/home/check_token`
- **描述**: 验证用户Token是否有效
- **Headers**: `Authorization: Bearer {token}`

## 2. 客户管理模块

### 2.1 获取客户列表
- **接口**: `GET /customer/index/index`
- **描述**: 获取客户列表，支持分页和搜索
- **参数**:
  ```
  ?page=1&limit=10&search=客户名称
  ```
- **响应**:
  ```json
  {
    "code": 1,
    "data": [
      {
        "id": 1,
        "name": "客户姓名",
        "mobile": "手机号",
        "province": "省份",
        "city": "城市",
        "area": "区域",
        "address": "详细地址",
        "is_create_project": 1  // 是否有项目：1-是，0-否
      }
    ]
  }
  ```

### 2.2 添加客户
- **接口**: `POST /customer/index/add`
- **描述**: 添加新客户
- **参数**:
  ```json
  {
    "name": "客户姓名",
    "mobile": "手机号",
    "province": "省份",
    "city": "城市", 
    "area": "区域",
    "address": "详细地址"
  }
  ```

### 2.3 编辑客户
- **接口**: `POST /customer/index/edit`
- **描述**: 编辑客户信息
- **参数**:
  ```json
  {
    "id": 1,
    "name": "客户姓名",
    "mobile": "手机号",
    "province": "省份",
    "city": "城市",
    "area": "区域", 
    "address": "详细地址"
  }
  ```

### 2.4 获取客户详情
- **接口**: `GET /customer/index/customer_info`
- **描述**: 获取指定客户的详细信息
- **参数**: `?id=1`

### 2.5 客户选择列表
- **接口**: `GET /customer/index/select_customer_list`
- **描述**: 获取用于选择的客户列表（简化信息）

## 3. 项目管理模块

### 3.1 项目基础接口

#### 3.1.1 获取项目列表
- **接口**: `GET /project/index/show_list`
- **描述**: 获取项目列表
- **参数**: `?search=项目名称`
- **响应**:
  ```json
  {
    "code": 1,
    "data": [
      {
        "id": 1,
        "project_name": "项目名称",
        "start_time": "2023-01-01",
        "end_time": "2023-12-31",
        "province": "省份",
        "city": "城市",
        "area": "区域",
        "address": "详细地址",
        "delayTasks": []  // 延期任务列表
      }
    ]
  }
  ```

#### 3.1.2 创建项目
- **接口**: `POST /project/index/create_project`
- **描述**: 创建新项目
- **参数**:
  ```json
  {
    "project_name": "项目名称",
    "customer_id": 1,
    "start_time": "2023-01-01",
    "end_time": "2023-12-31",
    "province": "省份",
    "city": "城市",
    "area": "区域",
    "address": "详细地址",
    "description": "项目描述"
  }
  ```

#### 3.1.3 获取项目详情
- **接口**: `GET /project/index/detail`
- **描述**: 获取项目详细信息
- **参数**: `?project_id=1`

#### 3.1.4 保存项目详情
- **接口**: `POST /project/index/save_detail`
- **描述**: 保存项目详细信息

#### 3.1.5 获取项目任务列表
- **接口**: `GET /project/index/task_list`
- **描述**: 获取项目的任务列表
- **参数**: `?project_id=1`

#### 3.1.6 开始任务
- **接口**: `POST /project/index/start_task`
- **描述**: 开始执行任务
- **参数**:
  ```json
  {
    "task_id": 1,
    "project_id": 1
  }
  ```

### 3.2 项目成员管理

#### 3.2.1 获取项目成员
- **接口**: `GET /project/index/project_member`
- **描述**: 获取项目成员列表
- **参数**: `?project_id=1`

#### 3.2.2 添加项目成员
- **接口**: `POST /project/index/insert_member`
- **描述**: 向项目添加成员
- **参数**:
  ```json
  {
    "project_id": 1,
    "user_id": 2,
    "role_id": 3
  }
  ```

#### 3.2.3 删除项目成员
- **接口**: `POST /project/index/delete_member`
- **描述**: 从项目中删除成员
- **参数**:
  ```json
  {
    "project_id": 1,
    "user_id": 2
  }
  ```

#### 3.2.4 获取角色列表
- **接口**: `GET /project/index/get_role_list`
- **描述**: 获取可分配的角色列表

#### 3.2.5 获取用户列表
- **接口**: `GET /project/index/get_user_list`
- **描述**: 获取可添加的用户列表

## 4. 方案阶段接口

### 4.1 方案管理
- **接口**: `GET /project/proposal/index`
- **描述**: 获取方案列表
- **参数**: `?project_id=1`

### 4.2 创建方案任务
- **接口**: `POST /project/proposal/create_proposal_task`
- **描述**: 创建方案任务
- **参数**:
  ```json
  {
    "project_id": 1,
    "task_name": "任务名称",
    "assign_user_id": 2,
    "deadline": "2023-12-31",
    "description": "任务描述"
  }
  ```

### 4.3 提交方案任务
- **接口**: `POST /project/proposal/submit_proposal_task`
- **描述**: 提交方案任务成果
- **参数**:
  ```json
  {
    "task_id": 1,
    "content": "提交内容",
    "files": ["文件路径"]
  }
  ```

### 4.4 审核方案任务
- **接口**: `POST /project/proposal/examine_proposal_task`
- **描述**: 审核方案任务
- **参数**:
  ```json
  {
    "task_id": 1,
    "status": "approved",  // approved-通过, rejected-拒绝
    "comment": "审核意见"
  }
  ```

### 4.5 导出方案
- **接口**: `POST /project/proposal/expload_proposal`
- **描述**: 导出方案文档

## 5. 设计阶段接口

### 5.1 设计管理
- **接口**: `GET /project/design/index`
- **描述**: 获取设计任务列表
- **参数**: `?project_id=1`

### 5.2 设计任务生命周期
- **创建前置**: `POST /project/design/before_create_task`
- **创建任务**: `POST /project/design/create_design_task`
- **创建后置**: `POST /project/design/after_create_task`
- **提交任务**: `POST /project/design/submit_design_task`
- **审核任务**: `POST /project/design/examine_design_task`

### 5.3 导出设计
- **接口**: `POST /project/design/expload_design`
- **描述**: 导出设计文档

## 6. 施工阶段接口

### 6.1 施工管理
- **接口**: `GET /project/construction/index`
- **描述**: 获取施工任务列表
- **参数**: `?project_id=1`

### 6.2 施工任务管理
- **创建前置**: `POST /project/construction/before_create_task`
- **创建任务**: `POST /project/construction/create_construction_task`
- **创建后置**: `POST /project/construction/after_create_task`
- **提交任务**: `POST /project/construction/submit_construction_task`
- **审核任务**: `POST /project/construction/examine_construction_task`

### 6.3 子进度管理
- **获取子进度**: `GET /project/construction/child_schedule`
- **提交子进度**: `POST /project/construction/submit_child_schedule`

### 6.4 普通任务
- **获取普通任务**: `GET /project/construction/get_ordinary_task`
- **提交普通任务**: `POST /project/construction/submit_ordinary_task`

## 7. 保障阶段接口

### 7.1 保障管理
- **接口**: `GET /project/ensure/index`
- **描述**: 获取保障任务列表

### 7.2 保障任务管理
- **创建前置**: `POST /project/ensure/before_create_task`
- **创建任务**: `POST /project/ensure/create_ensure_task`
- **创建后置**: `POST /project/ensure/after_create_task`
- **提交任务**: `POST /project/ensure/submit_ensure_task`
- **审核任务**: `POST /project/ensure/examine_ensure_task`

### 7.3 导出保障信息
- **接口**: `GET /project/ensure/expload_ensure`

## 8. 订单管理接口

### 8.1 订单基础
- **获取订单**: `GET /project/order/index`
- **保存订单**: `POST /project/order/save_index`

### 8.2 供应商管理
- **获取供应商**: `GET /project/order/get_supplier`

### 8.3 订单信息
- **获取订单信息**: `GET /project/order/project_order_info`
- **提交订单信息**: `POST /project/order/submit_project_order_info`

## 9. 周计划管理

### 9.1 周计划
- **获取周计划**: `GET /project/weekplan/index`
- **创建周计划**: `POST /project/weekplan/create_week_plan`

## 10. 文件管理

### 10.1 文件上传
- **接口**: `POST /index/home/saveFile`
- **描述**: 上传文件
- **Content-Type**: `multipart/form-data`
- **参数**:
  ```
  file: 文件对象
  ```

## 错误码说明

| 错误码 | 说明 |
|--------|------|
| 1 | 成功 |
| -1 | 失败 |
| 1001 | 用户未登录 |
| 1002 | 参数错误 |
| 1003 | 权限不足 |
| 1004 | 数据不存在 |

## 注意事项

1. **认证**: 除登录接口外，其他接口都需要在Header中携带Token
2. **参数格式**: POST请求使用 `application/x-www-form-urlencoded` 格式
3. **文件上传**: 使用 `multipart/form-data` 格式
4. **分页**: 列表接口支持 `page` 和 `limit` 参数
5. **搜索**: 支持 `search` 参数进行模糊搜索
