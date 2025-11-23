# 更新数据库location和postcode字段

## 问题说明

数据库中的`location`和`postcode`字段都是`null`，需要从房产详情页重新抓取并更新。

## 解决方案

### 1. 已修改Scrapper.py

**下次抓取时会自动提取location和postcode**：
- 从ld+json中提取地址信息
- 从页面文本中提取邮编
- 从地址区域提取地点名称
- 从URL中提取邮编（备用）

### 2. 创建更新脚本

**文件**: `backend/scripts/update_location_postcode.py`

功能：
- 重新抓取每个房产的详情页
- 提取location和postcode
- **只更新现有记录，不插入新记录**
- 批量提交，避免数据丢失

## 使用方法

### 运行更新脚本

```bash
cd backend
python scripts/update_location_postcode.py
```

或者在项目根目录：

```bash
python backend/scripts/update_location_postcode.py
```

### 脚本行为

1. **查找需要更新的记录**：所有`location`或`postcode`为空的房产
2. **重新抓取详情页**：对每个房产的URL进行抓取
3. **提取信息**：从HTML中提取location和postcode
4. **更新数据库**：只更新现有记录，每10条提交一次
5. **显示统计**：显示更新结果和覆盖率

### 提取方法

脚本会尝试多种方法提取：

1. **ld+json结构化数据**（最准确）
2. **页面文本中的邮编模式匹配**
3. **地址区域的地区名匹配**
4. **URL中的邮编提取**（备用）

## 示例输出

```
[INFO] 找到 100 条需要更新的房产记录
[INFO] 将重新抓取详情页提取location和postcode

[处理 1/100] ID: 1
  Title: Property for sale in Muswell Hill...
  📥 抓取: https://www.zoopla.co.uk/for-sale/details/...
  ✅ Location: Muswell Hill
  ✅ Postcode: N10

[进度] 已处理 10/100，已更新 8 条，已提交到数据库

[SUCCESS] 更新完成！
  - 总处理数: 100
  - 成功更新: 85
  - Postcode更新: 85
  - Location更新: 80
  - 失败/跳过: 15

[统计] 更新后的数据:
  - 总房产数: 100
  - 有postcode的: 85 (85.0%)
  - 有location的: 80 (80.0%)
```

## 注意事项

1. **请求频率控制**：脚本会在每次请求间随机延迟1-3秒，避免过快请求
2. **批量提交**：每10条更新提交一次，确保进度不丢失
3. **错误处理**：单条失败不影响整体进度
4. **不插入新记录**：脚本只更新现有记录，不会创建重复数据

## 性能

- **处理速度**：取决于网络速度，平均每条房产需要2-4秒
- **100条房产**：大约需要5-10分钟
- **大量数据**：可以分批运行，脚本支持断点续传（只更新空值）

## 后续验证

运行脚本后，可以测试AI搜索：

```sql
-- 查看N10的房产
SELECT COUNT(*) FROM properties WHERE postcode LIKE 'N10%';

-- 查看更新后的覆盖率
SELECT 
  COUNT(*) as total,
  SUM(CASE WHEN postcode IS NOT NULL AND postcode != '' THEN 1 ELSE 0 END) as with_postcode,
  SUM(CASE WHEN location IS NOT NULL AND location != '' THEN 1 ELSE 0 END) as with_location
FROM properties;
```

然后在小程序中输入"N10"测试AI搜索功能。








