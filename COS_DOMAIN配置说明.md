# COS_DOMAIN 配置说明

## 📋 字段说明

`COS_DOMAIN` 是**可选的**自定义域名，用于CDN加速和更好的访问体验。

## 🎯 如何填写

### 情况1: 没有自定义域名（推荐初学者）

**填写**：
```env
COS_DOMAIN=
```

或者：
```env
COS_DOMAIN=
```

**效果**：
- 使用COS默认域名
- 图片URL格式：`https://your-bucket.cos.ap-shanghai.myqcloud.com/path/to/image.jpg`
- 访问速度正常

---

### 情况2: 有CDN加速域名

**步骤**：
1. 在腾讯云控制台，进入 **CDN** 服务
2. 配置COS为源站
3. 添加加速域名（如 `images.yoursite.com`）

**填写**：
```env
COS_DOMAIN=https://images.yoursite.com
```

或者（不带协议）：
```env
COS_DOMAIN=images.yoursite.com
```

**效果**：
- 图片URL格式：`https://images.yoursite.com/path/to/image.jpg`
- 通过CDN访问，速度更快
- 适合微信小程序等对速度有要求的场景

---

### 情况3: 有自定义域名但没有配置CDN

**填写**：
```env
COS_DOMAIN=https://cdn.yoursite.com
```

**效果**：
- 使用自定义域名
- 需要手动配置CNAME指向COS

---

## ⚙️ 工作原理

### 代码逻辑

```python
# backend/utils/cos_uploader.py

# 如果设置了COS_DOMAIN
if self.domain:
    result_url = f"https://{self.domain}/{object_key}"
else:
    # 使用默认COS域名
    result_url = f"https://{self.bucket}.cos.{self.region}.myqcloud.com/{object_key}"
```

### 示例

**不设置COS_DOMAIN**（使用默认）：
```
上传到：property-images/2024/11/15/image.jpg
返回URL：https://property-images-1234567890.cos.ap-shanghai.myqcloud.com/property-images/2024/11/15/image.jpg
```

**设置COS_DOMAIN**：
```
上传到：property-images/2024/11/15/image.jpg
返回URL：https://images.yoursite.com/property-images/2024/11/15/image.jpg
```

---

## 🎯 推荐配置

### 开发环境（测试）

```env
# 留空，使用默认域名
COS_DOMAIN=
```

**优点**：
- ✅ 配置简单
- ✅ 无需额外设置
- ✅ 适合测试

---

### 生产环境（微信小程序）

如果希望图片加载更快：

1. **配置CDN加速**
2. **填写自定义域名**：

```env
COS_DOMAIN=https://images.yoursite.com
```

**优点**：
- ✅ 通过CDN加速
- ✅ 加载速度快
- ✅ 适合小程序

---

## 📝 实际填写示例

### 场景1: 本地开发

```env
COS_SECRET_ID=AKIDxxxxx
COS_SECRET_KEY=xxxxx
COS_REGION=ap-shanghai
COS_BUCKET=property-images
COS_DOMAIN=
```

✅ 最简单，适合初学者

---

### 场景2: 使用CDN加速

```env
COS_SECRET_ID=AKIDxxxxx
COS_SECRET_KEY=xxxxx
COS_REGION=ap-shanghai
COS_BUCKET=property-images
COS_DOMAIN=https://cdn-1251234567.cos.ap-shanghai.myqcloud.com
```

或：

```env
COS_DOMAIN=https://images.yoursite.com
```

✅ 快速加载

---

## 🔍 如何获取CDN域名

### 方法1: 查看COS默认域名

在COS控制台，找到存储桶详情：
```
默认域名：property-images-1234567890.cos.ap-shanghai.myqcloud.com
```

**但这个不是COS_DOMAIN**，COS_DOMAIN是可选的CDN加速域名。

### 方法2: 配置CDN加速

1. 在CDN控制台添加域名
2. 配置回源到COS
3. 获得CDN域名：`https://xyz-1234567890.cdn.com`

---

## ✅ 检查配置是否正确

### 填写 `.env` 后

运行爬虫：

```bash
python Scrapper.py
```

查看输出：

**正确输出**：
```
[COS] 上传成功: https://property-images-1234567890.cos.ap-shanghai.myqcloud.com/property-images/2024/11/15/image.jpg
```

**使用自定义域名时**：
```
[COS] 上传成功: https://your-cdn-domain.com/property-images/2024/11/15/image.jpg
```

---

## 🆘 常见问题

### Q1: COS_DOMAIN 必须填写吗？

**A**: 不必须。留空即可，会使用COS默认域名。

### Q2: 填写后图片显示不出来？

**A**: 
1. 检查域名是否正确
2. 确认CDN已配置
3. 检查CNAME配置

### Q3: 如何配置CDN？

**A**: 参考腾讯云CDN文档配置COS回源。

---

## 🎯 总结

| 使用场景 | COS_DOMAIN 填写 | 说明 |
|---------|----------------|------|
| 本地测试 | 留空或`""` | 最简单 |
| 开发环境 | 留空 | 使用默认域名 |
| 生产环境 | `https://your-cdn.com` | 需要配置CDN |

**推荐**：初学者直接留空 ✅

