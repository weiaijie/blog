# 辅助工具和脚本

## 工具概述

本文件夹包含低频量化投资系统的各种辅助工具和脚本，帮助自动化数据获取、处理和分析工作。

## 工具分类

### 1. 数据获取工具

#### 股票数据爬虫
- **文件名**：stock_data_crawler.py
- **功能**：自动获取股票基本面数据
- **数据源**：东方财富、新浪财经、雪球
- **更新频率**：每日自动运行
- **输出格式**：CSV、Excel

#### 转债数据获取
- **文件名**：bond_data_fetcher.py
- **功能**：获取可转债实时数据
- **数据源**：集思录、东方财富
- **包含数据**：价格、溢价率、到期收益率
- **更新频率**：实时或定时

#### 财务数据下载
- **文件名**：financial_data_downloader.py
- **功能**：批量下载财务报表数据
- **数据源**：理杏仁、萝卜投研
- **数据类型**：资产负债表、利润表、现金流量表
- **格式化**：自动整理为标准格式

### 2. 数据处理工具

#### 数据清洗脚本
- **文件名**：data_cleaner.py
- **功能**：清洗和标准化原始数据
- **处理内容**：
  - 去除异常值
  - 填补缺失值
  - 统一数据格式
  - 数据验证

#### 指标计算器
- **文件名**：indicator_calculator.py
- **功能**：计算各种技术和基本面指标
- **包含指标**：
  - PE、PB、ROE等基本面指标
  - MA、MACD等技术指标
  - 风险指标计算
  - 估值指标计算

#### 数据合并工具
- **文件名**：data_merger.py
- **功能**：合并多个数据源的数据
- **特点**：
  - 自动匹配股票代码
  - 处理时间序列对齐
  - 解决数据冲突
  - 生成统一数据集

### 3. 分析工具

#### 股票筛选器
- **文件名**：stock_screener.py
- **功能**：根据设定条件筛选股票
- **筛选条件**：
  - 基本面指标
  - 估值指标
  - 技术指标
  - 自定义条件

#### 估值计算器
- **文件名**：valuation_calculator.py
- **功能**：计算股票内在价值
- **估值方法**：
  - PE估值法
  - PB估值法
  - DCF估值法
  - 相对估值法

#### 风险分析器
- **文件名**：risk_analyzer.py
- **功能**：分析投资组合风险
- **分析内容**：
  - VaR计算
  - 最大回撤分析
  - 相关性分析
  - 压力测试

### 4. 自动化工具

#### 定时任务调度器
- **文件名**：task_scheduler.py
- **功能**：自动执行定时任务
- **任务类型**：
  - 数据更新
  - 报告生成
  - 风险检查
  - 提醒发送

#### 报告生成器
- **文件名**：report_generator.py
- **功能**：自动生成投资报告
- **报告类型**：
  - 日度简报
  - 周度总结
  - 月度报告
  - 年度总结

#### 邮件通知系统
- **文件名**：email_notifier.py
- **功能**：发送邮件通知
- **通知内容**：
  - 价格提醒
  - 风险预警
  - 报告推送
  - 系统状态

## 安装和配置

### 1. 环境要求
```python
Python 3.8+
pandas >= 1.3.0
numpy >= 1.21.0
requests >= 2.25.0
beautifulsoup4 >= 4.9.0
openpyxl >= 3.0.0
matplotlib >= 3.3.0
seaborn >= 0.11.0
```

### 2. 安装步骤
```bash
# 1. 克隆或下载工具包
git clone [repository_url]

# 2. 安装依赖包
pip install -r requirements.txt

# 3. 配置参数文件
cp config_template.py config.py
# 编辑config.py，设置个人参数

# 4. 测试运行
python test_tools.py
```

### 3. 配置文件说明
```python
# config.py 示例
DATABASE_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'username': 'your_username',
    'password': 'your_password',
    'database': 'investment_db'
}

EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'username': 'your_email@gmail.com',
    'password': 'your_app_password',
    'recipients': ['recipient@email.com']
}

API_CONFIG = {
    'tushare_token': 'your_tushare_token',
    'akshare_timeout': 30,
    'retry_times': 3
}
```

## 使用指南

### 1. 数据获取流程
```python
# 示例：获取股票数据
from tools.stock_data_crawler import StockDataCrawler

crawler = StockDataCrawler()
# 获取指定股票的数据
data = crawler.get_stock_data(['000001', '000002'])
# 保存到Excel
crawler.save_to_excel(data, 'stock_data.xlsx')
```

### 2. 股票筛选流程
```python
# 示例：筛选股票
from tools.stock_screener import StockScreener

screener = StockScreener()
# 设置筛选条件
conditions = {
    'pe_ratio': {'min': 0, 'max': 15},
    'pb_ratio': {'min': 0, 'max': 2},
    'roe': {'min': 10, 'max': 100},
    'market_cap': {'min': 10000000000}  # 100亿
}
# 执行筛选
results = screener.screen_stocks(conditions)
```

### 3. 自动化运行
```python
# 示例：设置定时任务
from tools.task_scheduler import TaskScheduler

scheduler = TaskScheduler()
# 每日9点更新数据
scheduler.add_daily_task('09:00', 'update_stock_data')
# 每周一生成报告
scheduler.add_weekly_task('Monday', '18:00', 'generate_weekly_report')
# 启动调度器
scheduler.start()
```

## 工具详细说明

### 1. 股票数据爬虫 (stock_data_crawler.py)

#### 主要功能
```python
class StockDataCrawler:
    def get_basic_info(self, stock_codes):
        """获取股票基本信息"""
        pass
    
    def get_financial_data(self, stock_codes):
        """获取财务数据"""
        pass
    
    def get_price_data(self, stock_codes, start_date, end_date):
        """获取价格数据"""
        pass
    
    def save_to_database(self, data):
        """保存到数据库"""
        pass
```

#### 使用示例
```python
crawler = StockDataCrawler()
# 获取沪深300成分股数据
hs300_codes = crawler.get_index_components('000300')
data = crawler.get_basic_info(hs300_codes)
crawler.save_to_excel(data, 'hs300_data.xlsx')
```

### 2. 估值计算器 (valuation_calculator.py)

#### 主要功能
```python
class ValuationCalculator:
    def pe_valuation(self, eps, pe_range):
        """PE估值法"""
        pass
    
    def pb_valuation(self, bvps, pb_range):
        """PB估值法"""
        pass
    
    def dcf_valuation(self, cash_flows, discount_rate):
        """DCF估值法"""
        pass
    
    def relative_valuation(self, stock_code, comparable_stocks):
        """相对估值法"""
        pass
```

### 3. 风险分析器 (risk_analyzer.py)

#### 主要功能
```python
class RiskAnalyzer:
    def calculate_var(self, returns, confidence_level=0.95):
        """计算VaR"""
        pass
    
    def max_drawdown(self, price_series):
        """计算最大回撤"""
        pass
    
    def correlation_analysis(self, portfolio):
        """相关性分析"""
        pass
    
    def stress_test(self, portfolio, scenarios):
        """压力测试"""
        pass
```

## 常见问题

### Q1：数据获取失败怎么办？
**解决方案：**
```python
# 1. 检查网络连接
# 2. 验证API密钥
# 3. 检查数据源是否正常
# 4. 使用备用数据源
```

### Q2：如何处理数据缺失？
**解决方案：**
```python
# 1. 使用前值填充
data.fillna(method='ffill')
# 2. 使用均值填充
data.fillna(data.mean())
# 3. 线性插值
data.interpolate()
```

### Q3：如何提高数据获取速度？
**解决方案：**
```python
# 1. 使用多线程
from concurrent.futures import ThreadPoolExecutor
# 2. 批量请求
# 3. 缓存机制
# 4. 增量更新
```

## 更新和维护

### 1. 版本更新
```
定期检查工具版本
更新依赖包版本
修复已知bug
添加新功能
```

### 2. 性能优化
```
优化算法效率
减少内存使用
提高运行速度
改进用户体验
```

### 3. 功能扩展
```
支持更多数据源
增加新的分析方法
完善自动化功能
提升系统稳定性
```
