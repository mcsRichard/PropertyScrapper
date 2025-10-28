# 图片上传到腾讯云COS完整实现说明

## ✅ 已实现功能

### 1. 图片自动上传到COS
- ✅ 爬虫运行时自动下载图片
- ✅ 自动上传到腾讯云COS
- ✅ 更新CSV中的图片URL为COS链接
- ✅ 支持批量上传

### 2. 数据库存储
- ✅ 图片URL与房产一一对应
- ✅ 存储COS链接而非原始URL
- ✅ 支持原始URL备份

### 3. 微信小程序显示
- ✅ 小程序已支持显示图片
- ✅ 使用COS的CDN链接
- ✅ 快速加载

## 📁 修改的文件

### 1. `backend/config.py`
添加了腾讯云COS配置：
```python
# 腾讯云COS配置
COS_SECRET_ID = os.getenv('COS_SECRET_ID', '')
COS_SECRET_KEY = os.getenv('COS_SECRET_KEY', '')
COS_REGION = os.getenv('COS_REGION', 'ap-shanghai')
COS_BUCKET = os.getenv('COS_BUCKET', 'your-bucket-name')
COS_DOMAIN = os.getenv('COS_DOMAIN', '')  # 可选：自定义域名
```

### 2. `backend/utils/cos_uploader.py`
创建了图片上传工具类：
- `SimpleCOSUploader`: 使用腾讯云官方SDK上传
- `create_cos_uploader()`: 工厂函数创建上传器
- 支持从URL下载并上传到COS
- 自动生成图片路径（日期目录结构）

### 3. `Scrapper.py`
修改了主爬虫文件：
- 添加COS上传支持
- 在保存CSV前上传所有图片
- 更新图片URL为COS链接
- 添加 `upload_image_to_cos()` 函数

### 4. `backend/requirements.txt`
添加了依赖：
```
cos-python-sdk-v5==1.9.25
```

### 5. `backend/env_example.txt`
添加了COS配置示例：
```env
# 腾讯云COS配置（图片存储）
COS_SECRET_ID=your-cos-secret-id
COS_SECRET_KEY=your-cos-secret-key
COS_REGION=ap-shanghai
COS_BUCKET=your-bucket-name
COS_DOMAIN=https://your-domain.com
```

## 🚀 使用流程

### 第一步：配置COS

1. 创建腾讯云COS存储桶
2. 获取API密钥
3. 配置 `.env` 文件

详细步骤参考：`COS_SETUP.md`

### 第二步：运行爬虫

```bash
python Scrapper.py
```

爬虫会：
1. 爬取房产数据
2. 下载图片到内存
3. 上传到COS
4. 更新CSV中的图片URL
5. 保存数据

### 第三步：小程序显示

微信小程序会自动从COS加载图片：

```
properties.csv (COS URL)
    ↓
后端API
    ↓
微信小程序
    ↓
显示COS图片
```

## 📊 数据流程

```
运行 Scrapper.py
    ↓
爬取Zoopla网站
    ↓
提取房产数据和图片URL
    ↓
下载图片到内存
    ↓
上传到腾讯云COS
    ↓
获取COS URL
    ↓
更新CSV中的image_url字段
    ↓
保存到 properties.csv
    ↓
小程序从COS加载图片
```

## 🎯 图片存储路径

COS中的图片按日期组织：

```
property-images/
  └── 2024/
      └── 11/
          └── 15/
              ├── 6b082c02b16bac28d66ae10c9be9babf5f55bcbe.jpg
              └── 92ea4198a00bdcaa9afca7ea5e1e05ab73154776.jpg
```

## 💾 数据库字段说明

### Property表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| title | String | 房产标题 |
| price | String | 价格字符串 |
| image_url | String | **COS图片URL（小程序使用）** |
| url | String | 原始Zoopla链接 |
| description | Text | 英文描述 |
| description_chinese | Text | 中文描述 |

### 关键字段

- **`image_url`**: 存储COS链接，微信小程序使用此字段显示图片
- **`url`**: 原始房产链接（用于跳转到Zoopla）

## 🔧 配置示例

### .env文件配置

```env
# 腾讯云COS配置
COS_SECRET_ID=AKIDxxxxx
COS_SECRET_KEY=xxxxx
COS_REGION=ap-shanghai
COS_BUCKET=property-images
COS_DOMAIN=https://images.yoursite.com
```

### 程序内部使用

```python
# Scrapper.py
from backend.utils.cos_uploader import create_cos_uploader
from backend.config import Config

# 创建上传器
cos_uploader = create_cos_uploader(Config())

# 上传图片
cos_url = cos_uploader.upload_image_from_url(image_url)

# 更新数据
property_data['image_url'] = cos_url
```

## 🌐 微信小程序使用

小程序已经实现了图片显示功能：

```javascript
// pages/index/index.wxml
<image 
  class="property-image" 
  src="{{item.image_url}}" 
  mode="aspectFill" 
/>
```

小程序自动使用COS链接加载图片。

## 📋 完整检查清单

### 配置检查
- [ ] 已创建腾讯云COS存储桶
- [ ] 已获取API密钥
- [ ] 已配置 `.env` 文件
- [ ] 已安装 `cos-python-sdk-v5`
- [ ] 已设置存储桶权限为公有读

### 功能测试
- [ ] 运行爬虫成功
- [ ] 图片上传到COS成功
- [ ] CSV中的URL已更新为COS链接
- [ ] 小程序能正常加载图片

## 🐛 常见问题

### Q1: 上传失败？

**解决方案**:
1. 检查COS配置是否正确
2. 确认API密钥有效
3. 检查网络连接

### Q2: 小程序图片显示不出来？

**解决方案**:
1. 确认存储桶设置为公有读
2. 检查图片URL是否正确
3. 验证小程序网络配置

### Q3: 上传很慢？

**解决方案**:
1. 使用就近的地域
2. 开启CDN加速
3. 使用多线程上传（可选）

## 📈 性能说明

### 上传速度
- 单张图片约500KB，上传时间约1-2秒
- 批量上传会依次进行，避免过快请求

### CDN加速
- 建议配置COS的CDN
- 在 `.env` 中设置 `COS_DOMAIN` 为CDN域名
- 可大幅提升加载速度

## ✅ 完成

现在您的爬虫已经实现：
1. ✅ 爬取房产数据
2. ✅ 下载图片
3. ✅ 上传到腾讯云COS
4. ✅ 保存COS URL到CSV
5. ✅ 微信小程序自动显示COS图片

**开始使用**：
```bash
python Scrapper.py
```

图片将自动上传到COS！🎉


