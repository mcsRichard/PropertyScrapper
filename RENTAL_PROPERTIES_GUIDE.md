# 添加出租房产功能指南

## 概述

本系统现在支持两个类别的房产信息：
- **出售房产** (for_sale)
- **出租房产** (for_rent)

## 数据库更改

### 新增字段
`properties` 表新增了 `listing_type` 字段：
- 类型: VARCHAR(20)
- 默认值: 'for_sale'
- 索引: 已创建
- 可能值: 'for_sale' 或 'for_rent'

### 运行数据库迁移

1. 进入项目根目录
2. 运行迁移脚本：

```bash
python backend/scripts/add_listing_type.py
```

这将自动：
- 检查 `listing_type` 列是否存在
- 如果不存在，添加列并创建索引
- 现有数据将默认设置为 'for_sale'

## 爬虫使用

### 爬取出售房产
```bash
python Scrapper.py --url "https://www.zoopla.co.uk/for-sale/property/n10/?q=N10&radius=1&search_source=for-sale"
```

### 爬取出租房产
```bash
python Scrapper.py --url "https://www.zoopla.co.uk/to-rent/property/n10/?q=N10&search_source=home" --output rental_properties.csv
```

### 爬虫功能
- 自动检测URL类型（出售或出租）
- 自动将 `listing_type` 添加到每个房产记录
- 支持自定义输出文件名
- 支持翻译描述为中文

## API 使用

### 获取出售房产
```http
GET /api/properties?listing_type=for_sale
```

### 获取出租房产
```http
GET /api/properties?listing_type=for_rent
```

### 获取所有房产（不指定 listing_type）
```http
GET /api/properties
```

### 其他筛选参数
所有现有筛选参数仍然有效：
- `page`: 页码
- `limit`: 每页数量
- `min_price`: 最低价格
- `max_price`: 最高价格
- `property_type`: 房产类型
- `bedrooms`: 卧室数量
- `location`: 位置

### 示例请求
```http
GET /api/properties?listing_type=for_rent&bedrooms=2&min_price=500&max_price=2000
```

## 小程序前端

### 功能说明

小程序首页现在包含一个分类切换器，用户可以：
1. **切换房产类型**: 点击"出售"或"出租"标签
2. **筛选**: 使用现有的筛选功能（卧室数量、房产类型、价格范围）
3. **搜索**: 搜索特定关键词

### UI更新

- 添加了房产类型切换标签（在搜索栏下方）
- 标签设计：选中状态为绿色背景，未选中为灰色
- 切换类型时自动刷新列表

### 数据结构

每个房产对象现在包含 `listing_type` 字段：
```javascript
{
  "id": 1,
  "title": "Property Title",
  "price": "£1,500 pcm",
  "listing_type": "for_rent",
  // ... 其他字段
}
```

## 导入数据

### 导入出售房产
```bash
python import_to_db.py
# 确保 properties.csv 包含出售房产数据
```

### 导入出租房产
```bash
# 1. 先爬取出租房产
python Scrapper.py --url "租房产URL" --output rental.csv

# 2. 修改 import_to_db.py 或直接导入
# 确保 CSV 文件包含 listing_type 列
python import_to_db.py
```

## 测试

### 测试API

```bash
# 测试获取出租房产
curl "http://localhost:5000/api/properties?listing_type=for_rent"

# 测试获取出售房产
curl "http://localhost:5000/api/properties?listing_type=for_sale"
```

### 测试小程序

1. 在微信开发者工具中打开项目
2. 运行小程序
3. 点击"出售"和"出租"标签切换
4. 验证筛选功能是否正常工作

## 注意事项

1. **数据库迁移**: 运行 `backend/scripts/add_listing_type.py` 前请备份数据库
2. **现有数据**: 现有房产数据将默认标记为 'for_sale'
3. **价格差异**: 出售价格通常为总额（如 £500,000），出租价格通常为月租金（如 £1,500 pcm）
4. **爬虫限制**: 请遵守Zoopla的服务条款和robots.txt规则

## 示例数据

### 出售房产示例
```
title: "3 bedroom flat for sale"
price: "£450,000"
listing_type: "for_sale"
```

### 出租房产示例
```
title: "2 bedroom flat to rent"
price: "£1,200 pcm"
listing_type: "for_rent"
```

## 故障排除

### 问题：小程序显示所有房产类型

**解决方案**: 确保前端代码已更新，检查 `listingType` 状态是否正确传递

### 问题：爬虫无法识别房产类型

**解决方案**: 确保URL包含 'to-rent' 或 'for-sale' 关键字

### 问题：API返回错误

**解决方案**: 
1. 检查数据库是否有 `listing_type` 列
2. 运行迁移脚本
3. 重启API服务器

## 开发团队

如有问题或建议，请联系开发团队。

