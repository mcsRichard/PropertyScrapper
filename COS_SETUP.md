# 腾讯云COS图片存储配置指南

## 📋 功能说明

本项目支持将爬取的房产图片自动上传到腾讯云对象存储（COS），并在微信小程序中显示。

## 🔧 配置步骤

### 1. 创建腾讯云COS存储桶

1. 登录 [腾讯云控制台](https://console.cloud.tencent.com/)
2. 进入 **对象存储 COS** 服务
3. 点击 **创建存储桶**
4. 填写以下信息：
   - **名称**: 例如 `property-images`
   - **地域**: 选择就近地域（如上海）
   - **访问权限**: 设置为 **公有读私有写** 或 **公有读写**
   - **存储类型**: 标准存储

### 2. 获取API密钥

#### 方法1: 通过控制台获取（推荐）

**步骤**：
1. 登录 [腾讯云控制台](https://console.cloud.tencent.com/)
2. 将鼠标悬停在右上角 **头像** 或 **用户名**
3. 在下拉菜单中点击 **访问管理** 或 **API密钥管理**
   - 或者直接访问：https://console.cloud.tencent.com/cam/capi
4. 在 **API密钥管理** 页面中：
   - 如果有现有密钥，直接查看并记录 `SecretId` 和 `SecretKey`
   - 如果没有，点击 **新建密钥** 创建
5. 复制并保存 `SecretId` 和 `SecretKey`（注意保密！）

#### 方法2: 直接链接访问

直接访问API密钥管理页面：
```
https://console.cloud.tencent.com/cam/capi
```

#### 方法3: 通过搜索找到

1. 在控制台顶部搜索框输入 "API密钥"
2. 选择 **访问管理 > API密钥管理**
3. 查看或创建密钥

#### 获取后的信息

- **SecretId**: 形如 `AKIDxxxxx`（公钥，可分享）
- **SecretKey**: 形如 `xxxxx`（私钥，必须保密）

### 3. 配置环境变量

编辑项目根目录的 `backend/.env` 文件（如果不存在，从 `env_example.txt` 复制）：

```bash
# 腾讯云COS配置
COS_SECRET_ID=your-cos-secret-id
COS_SECRET_KEY=your-cos-secret-key
COS_REGION=ap-shanghai
COS_BUCKET=your-bucket-name
COS_DOMAIN=https://your-domain.com  # 可选
```

**配置说明**：
- `COS_SECRET_ID`: 腾讯云API密钥ID
- `COS_SECRET_KEY`: 腾讯云API密钥KEY
- `COS_REGION`: 存储桶地域（如 `ap-shanghai`）
- `COS_BUCKET`: 存储桶名称（如 `property-images`）
- `COS_DOMAIN`: 自定义CDN域名（可选）

### 4. 安装依赖

```bash
pip install cos-python-sdk-v5
```

或在项目根目录：

```bash
cd backend
pip install -r requirements.txt
```

## 🚀 使用方法

### 自动上传（推荐）

运行爬虫时，图片会自动上传到COS：

```bash
python Scrapper.py
```

### 上传流程

```
爬取房产数据
    ↓
解析图片URL
    ↓
下载图片到内存
    ↓
上传到腾讯云COS
    ↓
更新CSV中的图片URL为COS URL
    ↓
保存到CSV文件
```

### 图片存储路径

COS中的图片存储路径格式：

```
property-images/
  └── 2024/
      └── 11/
          └── 15/
              ├── image_abc123.jpg
              └── image_def456.jpg
```

## 📊 图片URL格式

上传后的图片URL格式：

**使用默认域名**:
```
https://property-images-1234567890.cos.ap-shanghai.myqcloud.com/property-images/2024/11/15/image_abc123.jpg
```

**使用自定义域名**:
```
https://your-domain.com/property-images/2024/11/15/image_abc123.jpg
```

## 🔐 权限配置

### 推荐权限配置

在COS控制台设置访问权限：

1. **Bucket读写权限**: 公有读私有写（推荐）
2. **私有化读**: 如果需要保护图片

### CDN加速（可选）

1. 在COS控制台开通CDN
2. 配置加速域名
3. 在 `.env` 中设置 `COS_DOMAIN` 为CDN域名

## 📝 代码示例

### 使用腾讯云SDK上传

```python
from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client

# 配置信息
secret_id = 'your-secret-id'
secret_key = 'your-secret-key'
region = 'ap-shanghai'
config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key)
client = CosS3Client(config)

# 上传文件
response = client.put_object(
    Bucket='property-images',
    Body=image_data,
    Key='property-images/2024/11/15/image.jpg'
)
```

### 验证上传

在COS控制台的文件列表中查看上传的图片。

## 🎯 数据库字段说明

房产数据表中的图片URL字段：

- `image_url`: 存储在COS的图片URL（用于微信小程序显示）
- `original_image_url`: 原始Zoopla图片URL（备份）

## 🐛 故障排除

### 问题1: 上传失败

**解决方案**:
1. 检查COS配置是否正确
2. 确认SecretId和SecretKey有效
3. 检查存储桶权限设置

### 问题2: 图片显示不出来

**解决方案**:
1. 检查存储桶是否设置为公有读
2. 验证图片URL是否正确
3. 检查CDN配置（如使用）

### 问题3: 上传速度慢

**解决方案**:
1. 使用就近的地域
2. 开启COS的CDN加速
3. 使用多线程上传（开发中）

## 📈 性能优化

### 批量上传

项目支持自动批量上传所有爬取的图片，每张图片上传后替换CSV中的URL。

### 图片优化

建议在上传前优化图片：
1. 压缩图片大小（可选）
2. 统一图片格式（JPG/PNG）
3. 设置合适的图片尺寸

## 💰 费用说明

### COS存储费用

- 标准存储：约0.12元/GB/月
- 流量费用：约0.25元/GB（国内流量）
- 请求费用：PUT请求约0.0003元/万次

### 估算

假设：
- 每张图片 500KB
- 1000条房产数据
- 总大小约 500MB

**月费用**:
- 存储：约 0.06元
- 流量（1000次请求）：约 0.13元
- 总计：约 0.2元/月

## ✅ 完整配置检查清单

- [ ] 已创建COS存储桶
- [ ] 已获取API密钥
- [ ] 已配置 `.env` 文件
- [ ] 已安装 cos-python-sdk-v5
- [ ] 已设置存储桶权限为公有读
- [ ] 已测试上传功能

## 🎉 完成

配置完成后，运行爬虫即可自动上传图片到COS！

```bash
python Scrapper.py
```

图片将自动上传并替换CSV中的URL为COS链接。

