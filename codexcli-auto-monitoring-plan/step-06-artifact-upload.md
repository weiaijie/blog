# Step 06: 媒体上传与两阶段提交

## 目标

确保数据库记录与对象存储文件一致，不产生“有记录无文件”或“有文件无记录”。

## 前置条件

- Step 05 已产出本地 artifacts。

## 输入

- 本地 artifact 文件路径
- `run_id`、`step_id`

## 执行动作

1. 计算文件元数据：`sha256`、`size`、`mime_type`。
2. 调用 `POST /v1/artifacts/init` 获取预签名 URL。
3. 上传对象存储（S3/OSS/GCS）。
4. 调用 `POST /v1/artifacts/complete` 完成登记。
5. 发 `artifact.created` 事件。

## 关键字段

- `artifact_id`
- `object_key`
- `sha256`
- `size_bytes`
- `step_id`
- `source_path`（可选，内部调试）

## 产出

- 可下载 artifact 记录
- 可在时间线中关联到对应 `step`

## 验收标准

- 任意 artifact 都能通过 `artifact_id` 定位对象存储实体。
- `sha256` 校验一致率 100%。

## 失败处理

- 上传失败：重试（指数退避，上限重试次数）。
- `complete` 失败：进入补偿队列，定时重放完成登记请求。

