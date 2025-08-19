# Special 项目 Excel 上传功能详细分析

## 功能概述

Special项目中的Excel上传功能主要用于批量导入项目任务数据，支持三级任务层级的结构化数据导入。该功能通过解析Excel文件中的特定格式数据，自动创建项目的任务计划。

## 1. Excel数据格式规范

### 1.1 列映射定义
```javascript
// methods.js 中的列映射配置
let col = {
  // A: 'key',           // 预留列
  B: 'firstTaskName',    // 一级任务名称
  C: 'firstTaskDateStr', // 一级任务时间范围
  // D: 'secondKey',     // 预留列
  E: 'secondTaskName',   // 二级任务名称
  F: 'secondTaskDateStr',// 二级任务时间范围
  // G: 'thirdKey',      // 预留列
  H: 'thirdTaskName',    // 三级任务名称
  I: 'thirdTaskDateStr', // 三级任务时间范围
  J: 'executor',         // 执行人
  K: 'chargePerson',     // 负责人
  L: 'approver',         // 审批人
  M: 'content',          // 任务内容描述
}
```

### 1.2 Excel表格结构要求
```
| A | B(一级任务) | C(一级时间) | D | E(二级任务) | F(二级时间) | G | H(三级任务) | I(三级时间) | J(执行人) | K(负责人) | L(审批人) | M(内容) |
|---|------------|------------|---|------------|------------|---|------------|------------|----------|----------|----------|---------|
| 1 | 标题行      |            |   |            |            |   |            |            |          |          |          |         |
| 2 | 标题行      |            |   |            |            |   |            |            |          |          |          |         |
| 3 | 方案设计    | 2023-01-01~2023-01-15 |   | 初步方案   | 2023-01-01~2023-01-05 |   | 需求调研   | 2023-01-01~2023-01-02 | 张三     | 李四     | 王五     | 调研内容 |
```

### 1.3 时间格式要求
- **格式**: `YYYY-MM-DD~YYYY-MM-DD`
- **示例**: `2023-01-01~2023-01-15`
- **说明**: 开始时间和结束时间用波浪号(~)分隔

## 2. 核心解析逻辑

### 2.1 数据提取算法
```javascript
export async function loadExlcel(exlcelData, tableData) {
  let tempData = {}
  
  // 1. 遍历所有列映射
  for (let i in col) {
    for (let j in exlcelData) {
      let temp = {}
      let key = Number(j.substr(1)) // 提取行号
      
      // 2. 过滤有效数据行 (跳过前2行标题)
      if (!isNaN(key) && key > 2 && j.indexOf(i) != -1) {
        let data = exlcelData[j]
        temp[key] = data.v // 提取单元格值
      }
      
      // 3. 合并同列数据
      if (JSON.stringify(temp) != '{}') {
        tempData[i] = { ...tempData[i], ...temp }
      }
    }
  }
  
  return processTaskData(tempData, tableData)
}
```

### 2.2 时间格式验证
```javascript
// 严格的时间格式验证逻辑
const validateTimeFormat = (timeStr, taskName, level) => {
  // 1. 检查时间字符串是否存在
  if(!timeStr) {
    return {
      is_data: false,
      msg: `${taskName} 没有设置时间!`
    }
  }
  
  // 2. 检查时间分隔符
  if(!timeStr.includes('~')) {
    return {
      is_data: false,
      msg: `${taskName} 时间格式不正确，应为：开始时间~结束时间`
    }
  }
  
  // 3. 解析开始和结束时间
  const timeArray = timeStr.split('~')
  if(timeArray.length !== 2) {
    return {
      is_data: false,
      msg: `${taskName} 时间格式不正确!`
    }
  }
  
  // 4. 验证日期有效性
  const startTime = new Date(timeArray[0])
  const endTime = new Date(timeArray[1])
  
  if(isNaN(startTime.getTime()) || isNaN(endTime.getTime())) {
    return {
      is_data: false,
      msg: `${taskName} ${timeStr} 时间格式不正确!`
    }
  }
  
  // 5. 验证时间逻辑
  if(startTime >= endTime) {
    return {
      is_data: false,
      msg: `${taskName} 开始时间必须早于结束时间!`
    }
  }
  
  return { is_data: true }
}
```

## 3. 任务层级处理

### 3.1 三级任务结构
```javascript
// 任务数据结构定义
let firstTask = {
  rows: [],           // 行号信息
  data: [],          // 一级任务数据
  relationData: []   // 关联关系数据
}

let secondaryTask = {
  rows: [],          // 行号信息
  data: [],          // 二级任务数据
  relationData: []   // 关联关系数据
}

let threeTask = {
  rows: [],          // 行号信息
  data: []           // 三级任务数据
}
```

### 3.2 任务关联逻辑
```javascript
// 处理任务父子关系
const processTaskRelations = () => {
  // 1. 处理一级任务的合并单元格信息
  for (let i in firstTask.data) {
    exlcelData['!merges'].forEach((item) => {
      if (item.s.r == Number(firstTask.data[i].row) - 1 && 
          item.s.c == 1 && item.e.c == 1) {
        firstTask.data[i] = {
          ...firstTask.data[i],
          startRow: item.s.r + 1,  // 开始行号
          endRow: item.e.r + 1,    // 结束行号
          numRow: (item.e.r - item.s.r) + 1  // 包含行数
        }
      }
    })
  }
  
  // 2. 给二级任务设置父任务ID (taskpid)
  firstTask.data.map((firstItem) => {
    secondaryTask.data.map((item) => {
      if (firstItem.startRow <= item.row && item.row <= firstItem.endRow) {
        item.taskpid = firstItem.id
      } else if (firstItem.row == item.row) {
        item.taskpid = firstItem.id
      }
    })
  })
  
  // 3. 给三级任务设置父任务ID
  secondaryTask.data.map((secondItem) => {
    threeTask.data.map((item) => {
      if (secondItem.startRow <= item.row && item.row <= secondItem.endRow) {
        item.taskpid = secondItem.id
      } else if (secondItem.row == item.row) {
        item.taskpid = secondItem.id
      }
    })
  })
}
```

## 4. 数据验证机制

### 4.1 必填字段验证
```javascript
const validateRequiredFields = (taskData) => {
  const requiredFields = {
    firstTask: ['firstTaskName', 'firstTaskDateStr'],
    secondTask: ['secondTaskName', 'secondTaskDateStr'],
    thirdTask: ['thirdTaskName', 'thirdTaskDateStr', 'executor']
  }
  
  // 验证每个任务的必填字段
  for(let task of taskData) {
    const fields = requiredFields[task.level + 'Task']
    for(let field of fields) {
      if(!task[field] || task[field].trim() === '') {
        return {
          valid: false,
          message: `${task.task_name || '任务'} 的 ${field} 字段不能为空`
        }
      }
    }
  }
  
  return { valid: true }
}
```

### 4.2 数据完整性检查
```javascript
const validateDataIntegrity = (excelData) => {
  let message = { is_data: true, msg: '' }
  
  for (let i in col) {
    if (message.is_data == false) break
    
    for (let j in tempData[i]) {
      // 一级和二级任务验证
      if (i == "B" || i == "E") {
        let level = { B: 1, E: 2 }
        let time = { '1': 'C', '2': 'F' }
        
        // 检查对应的时间列是否存在
        if(tempData[time[level[i]]][j] == undefined){
          let taskName = level[i] == 1 ? tempData["B"][j] : tempData["E"][j]
          message.msg = `${taskName} 没有设置时间!`
          message.is_data = false
          break
        }
        
        // 验证时间格式
        const timeValidation = validateTimeFormat(
          tempData[time[level[i]]][j], 
          level[i] == 1 ? tempData["B"][j] : tempData["E"][j]
        )
        
        if(!timeValidation.is_data) {
          message = timeValidation
          break
        }
      }
      
      // 三级任务验证
      if (i == "H") {
        const timeValidation = validateTimeFormat(
          tempData['I'][j], 
          tempData['J'][j]
        )
        
        if(!timeValidation.is_data) {
          message = timeValidation
          break
        }
      }
    }
  }
  
  return message
}
```

## 5. 错误处理机制

### 5.1 解析错误处理
```javascript
const handleParseErrors = (error, rowIndex, columnIndex) => {
  const errorTypes = {
    INVALID_DATE: '日期格式错误',
    MISSING_REQUIRED: '必填字段缺失',
    INVALID_STRUCTURE: '表格结构错误',
    ENCODING_ERROR: '文件编码错误'
  }
  
  return {
    code: -1,
    message: `第${rowIndex}行第${columnIndex}列: ${errorTypes[error.type] || '未知错误'}`,
    details: error.details
  }
}
```

### 5.2 用户友好的错误提示
```javascript
const generateUserFriendlyError = (validationResult) => {
  if(!validationResult.is_data) {
    // 根据错误类型生成具体的修复建议
    if(validationResult.msg.includes('时间格式')) {
      return {
        title: '时间格式错误',
        message: validationResult.msg,
        suggestion: '请确保时间格式为：YYYY-MM-DD~YYYY-MM-DD，例如：2023-01-01~2023-01-15'
      }
    } else if(validationResult.msg.includes('没有设置时间')) {
      return {
        title: '缺少时间信息',
        message: validationResult.msg,
        suggestion: '请为每个任务设置开始时间和结束时间'
      }
    }
  }
  
  return { success: true }
}
```

## 6. 性能优化

### 6.1 大文件处理
```javascript
const processLargeExcel = async (excelData) => {
  const CHUNK_SIZE = 1000 // 每次处理1000行
  const totalRows = Object.keys(excelData).length
  const chunks = Math.ceil(totalRows / CHUNK_SIZE)
  
  let processedData = []
  
  for(let i = 0; i < chunks; i++) {
    const startRow = i * CHUNK_SIZE
    const endRow = Math.min(startRow + CHUNK_SIZE, totalRows)
    
    // 分块处理数据
    const chunkData = await processChunk(excelData, startRow, endRow)
    processedData = processedData.concat(chunkData)
    
    // 显示进度
    const progress = Math.round((i + 1) / chunks * 100)
    updateProgress(progress)
  }
  
  return processedData
}
```

### 6.2 内存优化
```javascript
const optimizeMemoryUsage = () => {
  // 及时清理临时数据
  tempData = null
  firstTask = null
  secondaryTask = null
  threeTask = null
  
  // 强制垃圾回收（在支持的环境中）
  if(global.gc) {
    global.gc()
  }
}
```

## 7. 使用场景和限制

### 7.1 适用场景
- **项目初始化**: 快速导入项目的完整任务计划
- **模板应用**: 使用标准模板创建相似项目
- **批量更新**: 批量修改任务信息和时间安排
- **数据迁移**: 从其他系统迁移任务数据

### 7.2 功能限制
- **文件格式**: 仅支持Excel格式 (.xlsx, .xls)
- **文件大小**: 建议不超过10MB
- **行数限制**: 建议不超过5000行
- **列结构**: 必须严格按照预定义的列结构
- **时间格式**: 必须使用指定的时间格式

### 7.3 最佳实践
1. **模板使用**: 提供标准Excel模板供用户下载
2. **数据验证**: 上传前进行客户端预验证
3. **分步导入**: 大量数据分批次导入
4. **备份机制**: 导入前备份现有数据
5. **日志记录**: 记录导入过程和结果

## 8. 扩展建议

### 8.1 功能增强
- **多格式支持**: 支持CSV、JSON等格式
- **在线编辑**: 提供在线表格编辑器
- **模板管理**: 支持自定义模板保存和管理
- **导入预览**: 导入前预览解析结果

### 8.2 用户体验优化
- **拖拽上传**: 支持拖拽文件上传
- **进度显示**: 显示详细的导入进度
- **错误定位**: 精确定位错误位置
- **批量操作**: 支持批量文件处理

这个Excel上传功能体现了Special项目在数据处理方面的专业性，通过严格的格式规范和完善的验证机制，确保了任务数据的准确性和完整性。
