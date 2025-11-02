# 修复数据库location和postcode字段

## 问题说明

数据库中的`location`和`postcode`字段都是`null`，导致AI搜索无法找到房产。

## 解决方案

已创建修复脚本 `backend/scripts/fix_location_postcode.py`，该脚本会：

1. **从title中提取邮编和地点**
   - 提取英国邮编格式（如 N10, SW7, N10 1AB）
   - 提取常见伦敦地区名称（如 Muswell Hill, Hampstead）

2. **从description中提取**（如果title中没有）

3. **从URL中提取**（如果前两者都没有）

## 使用方法

### 1. 运行修复脚本

```bash
cd backend
python scripts/fix_location_postcode.py
```

或者在项目根目录：

```bash
python backend/scripts/fix_location_postcode.py
```

### 2. 查看输出

脚本会显示：
- 找到多少条需要修复的记录
- 每条记录的修复情况
- 修复后的统计信息

### 3. 验证修复结果

运行脚本后，可以在数据库中查询：

```sql
-- 查看有postcode的房产数量
SELECT COUNT(*) FROM properties WHERE postcode IS NOT NULL AND postcode != '';

-- 查看有location的房产数量
SELECT COUNT(*) FROM properties WHERE location IS NOT NULL AND location != '';

-- 查看N10的房产
SELECT COUNT(*) FROM properties WHERE postcode LIKE 'N10%';
```

## 脚本功能

### 邮编提取规则

1. **完整邮编格式**：`N10 1AB`, `SW7 3AZ`
2. **邮编前缀**：`N10`, `SW7`, `WC1`

### 地点提取规则

1. **常见伦敦地区**：Muswell Hill, Hampstead, Camden等
2. **标题模式匹配**：
   - "Property in [Location]"
   - "Street, Location"
   - "Location London"

## 示例输出

```
[INFO] 找到 100 条需要修复的房产记录

[处理 1/100] ID: 1, Title: Property for sale in Muswell Hill, London N10...
  ✅ Postcode: None -> N10
  ✅ Location: None -> Muswell Hill

[SUCCESS] 修复完成！
  - 总更新数: 95
  - Postcode更新数: 95
  - Location更新数: 80

[统计] 修复后的数据:
  - 总房产数: 100
  - 有postcode的: 95 (95.0%)
  - 有location的: 80 (80.0%)
```

## 注意事项

1. **数据备份**：建议在运行脚本前备份数据库
2. **部分数据可能无法修复**：如果title/description中没有地址信息，这些记录仍会保持为null
3. **后续抓取**：建议更新`Scrapper.py`，在抓取时就提取location和postcode

## 后续优化

可以考虑：
1. 更新`Scrapper.py`，在抓取时就提取location和postcode
2. 使用Nominatim API从地址文本中提取邮编
3. 添加更多地点识别规则

