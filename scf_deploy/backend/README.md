# Property Scraper Backend API

## 功能特性

- ✅ 房产数据存储和管理
- ✅ RESTful API接口
- ✅ 分页查询和筛选
- ✅ 搜索功能
- ✅ 数据导入导出
- ✅ 中文翻译支持

## 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置数据库

复制 `env_example.txt` 为 `.env` 并填入您的TDSQL-C配置：

```bash
cp env_example.txt .env
```

编辑 `.env` 文件：
```
DB_HOST=your-tdsql-endpoint.tencentcloudapi.com
DB_PORT=3306
DB_USER=your-username
DB_PASSWORD=your-password
DB_NAME=properties
```

### 3. 初始化数据库

```bash
python app.py
```

### 4. 导入数据

```bash
python scripts/import_data.py ../properties.csv
```

### 5. 启动API服务

```bash
python app.py
```

## API接口

### 房产相关

- `GET /api/properties` - 获取房产列表
- `GET /api/properties/{id}` - 获取房产详情
- `GET /api/properties/search` - 搜索房产
- `GET /api/properties/filters` - 获取筛选选项

### 管理接口

- `POST /api/admin/import-properties` - 导入房产数据
- `PUT /api/admin/properties/{id}` - 更新房产数据
- `DELETE /api/admin/properties/{id}` - 删除房产数据
- `GET /api/admin/stats` - 获取统计信息

## 使用示例

### 获取房产列表

```bash
curl "http://localhost:5000/api/properties?page=1&limit=20&min_price=100000&max_price=500000"
```

### 搜索房产

```bash
curl "http://localhost:5000/api/properties/search?keyword=flat&page=1&limit=10"
```

### 获取筛选选项

```bash
curl "http://localhost:5000/api/properties/filters"
```

## 数据库结构

### properties 表
- id: 主键
- title: 房产标题
- price: 价格字符串
- price_numeric: 数字价格（用于排序）
- bedrooms: 卧室数量
- bathrooms: 浴室数量
- property_type: 房产类型
- location: 位置
- description: 英文描述
- description_chinese: 中文描述
- url: 原始链接
- image_url: 图片链接

## 部署到腾讯云

### 1. 部署到SCF

```bash
# 安装SCF CLI
npm install -g @cloudbase/cli

# 部署
tcb functions:deploy property-api
```

### 2. 配置域名

在腾讯云控制台配置已备案域名，指向SCF函数。

## 注意事项

- 确保TDSQL-C数据库已创建
- 确保网络连接正常
- 建议使用HTTPS部署
- 定期备份数据库
