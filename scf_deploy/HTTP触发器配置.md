# HTTP触发器配置说明

## 📋 配置步骤

### 步骤1: 创建HTTP触发器

1. **登录腾讯云控制台**
   - 访问：https://console.cloud.tencent.com/scf

2. **进入云函数**
   - 找到你的函数（如：property-api）
   - 点击函数名称进入详情

3. **进入触发器管理**
   - 点击"触发器管理"标签
   - 点击"创建触发器"

4. **配置触发器**
   - **触发方式**：选择 `API Gateway触发器`
   - **API网关**：选择"新建API网关服务"或使用已有服务
   - **请求方法**：选择 `ANY`（支持所有HTTP方法）
   - **发布环境**：选择 `发布`（生产环境）
   - **路径配置**：选择 `/{proxy+}` 或 `/api/{proxy+}`
     - `/{proxy+}` - 匹配所有路径
     - `/api/{proxy+}` - 只匹配/api/开头的路径
   - **启用CORS**：✅ 勾选（小程序需要跨域支持）

5. **保存配置**
   - 点击"完成"
   - 等待触发器创建完成

---

## 🔧 详细配置说明

### 触发方式：API Gateway触发器

API Gateway触发器会将HTTP请求转发给云函数，适合Web函数（Flask应用）。

### 路径配置

#### 选项1: `/{proxy+}`（推荐）

**优点**：
- 匹配所有路径
- 包括 `/`、`/health`、`/api/properties` 等所有路径

**配置**：
```
路径：/{proxy+}
```

**访问示例**：
- `https://your-domain.com/` → 根路径
- `https://your-domain.com/health` → 健康检查
- `https://your-domain.com/api/properties` → API接口

#### 选项2: `/api/{proxy+}`

**优点**：
- 只匹配API路径
- 更安全，避免暴露其他路径

**配置**：
```
路径：/api/{proxy+}
```

**访问示例**：
- `https://your-domain.com/api/properties` → ✅ 可以访问
- `https://your-domain.com/health` → ❌ 无法访问（需要单独配置）

**如果选择此选项，需要额外配置**：
- 为 `/health` 单独创建一个触发器
- 或修改Flask应用，将健康检查放在 `/api/health`

### 请求方法：ANY

选择 `ANY` 支持所有HTTP方法（GET、POST、PUT、DELETE等），Flask应用需要支持多种方法。

### 启用CORS

**必须勾选**，因为：
- 小程序需要跨域访问API
- 浏览器会进行CORS检查
- 不启用会导致跨域错误

---

## 🌐 域名配置（备案完成后）

### 步骤1: 绑定域名

1. **进入API网关控制台**
   - 访问：https://console.cloud.tencent.com/apigateway

2. **找到API网关服务**
   - 找到HTTP触发器创建的API网关服务

3. **绑定自定义域名**
   - 点击"自定义域名"
   - 点击"新建"
   - 输入已备案的域名（如：`api.yoursite.com`）
   - 选择协议：`HTTPS`
   - 选择SSL证书（需要先申请）

4. **配置路径映射**
   - 默认路径：`/`
   - 映射到：你的API服务

### 步骤2: 配置DNS解析

1. **进入域名DNS管理**
   - 在域名服务商处配置DNS

2. **添加CNAME记录**
   - 记录类型：`CNAME`
   - 主机记录：`api`（或你想要的子域名）
   - 记录值：API网关提供的CNAME地址

3. **等待DNS生效**
   - 通常几分钟到几小时

### 步骤3: 申请SSL证书

1. **进入SSL证书服务**
   - 访问：https://console.cloud.tencent.com/ssl

2. **申请免费证书**
   - 点击"申请免费证书"
   - 选择域名类型：`单域名`
   - 输入域名：`api.yoursite.com`
   - 完成域名验证

3. **等待证书签发**
   - 通常0.5-2小时

4. **绑定证书到API网关**
   - 在API网关的自定义域名中
   - 选择刚申请的SSL证书

---

## ✅ 验证配置

### 1. 测试临时域名

HTTP触发器创建后，会生成一个临时域名：
```
https://service-xxx-xxx.apigw.tencentcs.com/...
```

**测试**：
```bash
# 健康检查
curl https://service-xxx-xxx.apigw.tencentcs.com/health

# API接口
curl https://service-xxx-xxx.apigw.tencentcs.com/api/properties?page=1&limit=10
```

### 2. 测试自定义域名（配置后）

```bash
# 健康检查
curl https://api.yoursite.com/health

# API接口
curl https://api.yoursite.com/api/properties?page=1&limit=10
```

**预期返回**：
- 健康检查：`{"status": "healthy", "message": "Property API is running"}`
- API接口：房产列表JSON数据

---

## 🔍 路径映射说明

### Flask应用路径 vs API网关路径

**Flask应用中的路径**：
- `/` - 根路径
- `/health` - 健康检查
- `/api/properties` - 房产列表
- `/api/properties/<id>` - 房产详情

**API网关路径配置**：

#### 如果使用 `/{proxy+}`：
- `https://your-domain.com/` → Flask `/`
- `https://your-domain.com/health` → Flask `/health`
- `https://your-domain.com/api/properties` → Flask `/api/properties`

#### 如果使用 `/api/{proxy+}`：
- `https://your-domain.com/api/properties` → Flask `/api/properties`
- `https://your-domain.com/health` → ❌ 无法访问

**推荐使用 `/{proxy+}`**，这样可以访问所有路径。

---

## ⚠️ 注意事项

1. **必须使用HTTPS**
   - 小程序要求HTTPS
   - 不能使用HTTP

2. **域名必须备案**
   - 境内服务器必须备案
   - 备案通过后才能绑定域名

3. **CORS必须启用**
   - 小程序需要跨域支持
   - 不启用会导致请求失败

4. **路径配置要正确**
   - 确保路径能匹配到Flask应用的所有路由
   - 推荐使用 `/{proxy+}`

---

## 🆘 常见问题

### Q1: 访问返回404？
**检查**：
- 路径配置是否正确
- Flask应用路由是否正确
- 是否使用了 `/api/{proxy+}` 但访问了非 `/api/` 路径

### Q2: 访问返回CORS错误？
**解决**：
- 确认已启用CORS
- 检查Flask应用中的CORS配置
- 确认小程序域名已配置

### Q3: 域名无法访问？
**检查**：
- DNS解析是否正确
- SSL证书是否已绑定
- 域名是否已备案
- API网关服务是否正常运行

### Q4: 如何查看API网关地址？
**方法**：
- 在云函数触发器管理中查看
- 在API网关控制台查看
- 临时域名格式：`https://service-xxx-xxx.apigw.tencentcs.com`

