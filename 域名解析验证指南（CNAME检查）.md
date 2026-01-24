# 域名解析验证指南（CNAME检查）

## 📋 确认域名解析到API网关的步骤

### 第一步：获取API网关的CNAME地址

#### 1.1 登录腾讯云控制台
- 访问：https://console.cloud.tencent.com/apigateway
- 登录你的腾讯云账号

#### 1.2 找到API网关服务
1. 进入"API网关"控制台
2. 找到你的API网关服务（通常名称包含你的云函数名称）
3. 点击服务名称进入详情

#### 1.3 查看自定义域名配置
1. 点击左侧菜单"自定义域名"
2. 如果已绑定域名，会显示：
   - **域名**：你的域名（如：`api.yoursite.com`）
   - **CNAME地址**：类似 `xxx.apigw.tencentcs.com` 的地址
   - **状态**：已绑定/未绑定

#### 1.4 如果还没有绑定域名
1. 点击"新建"或"绑定域名"
2. 输入你的已备案域名
3. 选择协议：`HTTPS`
4. 选择SSL证书（需要先申请）
5. 保存后，系统会显示**CNAME地址**

**记录这个CNAME地址**，格式类似：
```
xxx-xxx-xxx.apigw.tencentcs.com
```

---

### 第二步：检查DNS解析配置

#### 2.1 登录域名管理控制台
- 如果域名在腾讯云：访问 https://console.cloud.tencent.com/cns
- 如果域名在其他服务商：登录对应的域名管理控制台

#### 2.2 找到DNS解析设置
1. 找到你的域名
2. 点击"解析"或"DNS解析"
3. 查看现有的解析记录

#### 2.3 检查CNAME记录
查找是否有以下记录：

**记录类型**：`CNAME`  
**主机记录**：`api`（或你使用的子域名，如：`www`、`@`等）  
**记录值**：应该是API网关提供的CNAME地址（如：`xxx-xxx-xxx.apigw.tencentcs.com`）

#### 2.4 如果没有CNAME记录，需要添加
1. 点击"添加记录"
2. 填写信息：
   - **记录类型**：选择 `CNAME`
   - **主机记录**：填写子域名（如：`api`）
     - 如果使用 `api.yoursite.com`，主机记录填 `api`
     - 如果使用 `www.yoursite.com`，主机记录填 `www`
     - 如果使用根域名 `yoursite.com`，主机记录填 `@`
   - **记录值**：粘贴API网关提供的CNAME地址
   - **TTL**：默认600秒（10分钟）
3. 点击"保存"

---

### 第三步：验证DNS解析是否生效

#### 3.1 使用命令行工具检查（推荐）

**Windows PowerShell**：
```powershell
# 检查CNAME记录
nslookup api.yoursite.com

# 或使用
Resolve-DnsName api.yoursite.com -Type CNAME
```

**Mac/Linux**：
```bash
# 检查CNAME记录
dig api.yoursite.com CNAME

# 或使用
nslookup api.yoursite.com
```

**预期输出**：
```
api.yoursite.com canonical name = xxx-xxx-xxx.apigw.tencentcs.com
```

#### 3.2 使用在线工具检查

**推荐工具**：
1. **DNS查询工具**：https://tool.chinaz.com/dns
2. **站长工具**：https://tool.chinaz.com/dns/?type=1
3. **腾讯云DNS检测**：https://console.cloud.tencent.com/cns

**操作步骤**：
1. 输入你的域名（如：`api.yoursite.com`）
2. 选择记录类型：`CNAME`
3. 点击查询
4. 查看返回的CNAME记录值

**预期结果**：
- 应该显示API网关的CNAME地址
- 格式：`xxx-xxx-xxx.apigw.tencentcs.com`

#### 3.3 检查解析状态

**正常状态**：
- ✅ CNAME记录存在
- ✅ 记录值指向API网关CNAME地址
- ✅ TTL已设置

**异常状态**：
- ❌ 没有CNAME记录
- ❌ 记录值不正确
- ❌ 记录值指向其他地址

---

### 第四步：测试域名访问

#### 4.1 测试HTTPS访问

**使用浏览器**：
1. 打开浏览器
2. 访问：`https://api.yoursite.com/health`
3. 查看是否能正常访问

**使用命令行**：
```bash
# Windows PowerShell
Invoke-WebRequest -Uri "https://api.yoursite.com/health" -Method GET

# Mac/Linux
curl https://api.yoursite.com/health
```

**预期返回**：
```json
{
  "status": "healthy",
  "message": "Property API is running"
}
```

#### 4.2 测试API接口

```bash
# 测试房产列表接口
curl https://api.yoursite.com/api/properties?page=1&limit=10
```

**预期返回**：房产列表JSON数据

#### 4.3 检查SSL证书

**在浏览器中**：
1. 访问 `https://api.yoursite.com`
2. 点击地址栏的锁图标
3. 查看证书信息
4. 确认证书有效且域名匹配

**正常状态**：
- ✅ 显示绿色锁图标
- ✅ 证书有效
- ✅ 域名匹配

---

### 第五步：常见问题排查

#### 问题1：DNS解析未生效

**症状**：
- `nslookup` 查询不到CNAME记录
- 域名无法访问

**可能原因**：
- DNS记录刚添加，还未生效（通常几分钟到几小时）
- DNS记录配置错误
- TTL设置过长

**解决方法**：
1. 等待DNS生效（通常10分钟-2小时）
2. 检查DNS记录配置是否正确
3. 将TTL设置为较短时间（如300秒）以便快速生效

#### 问题2：CNAME记录值不正确

**症状**：
- DNS解析返回的CNAME地址不是API网关地址

**解决方法**：
1. 确认API网关的CNAME地址
2. 更新DNS记录值为正确的CNAME地址
3. 等待DNS生效

#### 问题3：域名可以解析但无法访问

**可能原因**：
- SSL证书未绑定
- API网关未绑定域名
- 路径映射配置错误

**解决方法**：
1. 检查API网关中域名是否已绑定
2. 检查SSL证书是否已绑定
3. 检查路径映射配置

#### 问题4：SSL证书错误

**症状**：
- 浏览器显示"不安全"或证书错误

**解决方法**：
1. 确认SSL证书已申请并签发
2. 确认SSL证书已绑定到API网关
3. 确认证书域名与访问域名匹配

---

## ✅ 验证检查清单

### DNS解析检查
- [ ] 已获取API网关的CNAME地址
- [ ] 已在DNS管理中添加CNAME记录
- [ ] CNAME记录值正确（指向API网关地址）
- [ ] 使用 `nslookup` 或 `dig` 可以查询到CNAME记录
- [ ] DNS解析已生效（通常10分钟-2小时）

### 域名访问检查
- [ ] 可以通过HTTPS访问域名
- [ ] 健康检查接口返回正常：`https://api.yoursite.com/health`
- [ ] API接口可以正常访问：`https://api.yoursite.com/api/properties`
- [ ] SSL证书有效（浏览器显示绿色锁图标）

### API网关配置检查
- [ ] 域名已在API网关中绑定
- [ ] SSL证书已绑定到API网关
- [ ] 路径映射配置正确
- [ ] CORS已启用

---

## 🔍 快速验证命令

### Windows PowerShell
```powershell
# 1. 检查DNS解析
Resolve-DnsName api.yoursite.com -Type CNAME

# 2. 测试健康检查
Invoke-WebRequest -Uri "https://api.yoursite.com/health" -Method GET

# 3. 测试API接口
Invoke-WebRequest -Uri "https://api.yoursite.com/api/properties?page=1&limit=10" -Method GET
```

### Mac/Linux
```bash
# 1. 检查DNS解析
dig api.yoursite.com CNAME

# 2. 测试健康检查
curl https://api.yoursite.com/health

# 3. 测试API接口
curl https://api.yoursite.com/api/properties?page=1&limit=10
```

### 在线工具
- DNS查询：https://tool.chinaz.com/dns
- SSL检查：https://myssl.com/
- 网站测速：https://tool.chinaz.com/speedtest

---

## 📞 需要帮助？

### 如果DNS解析有问题
1. **检查DNS记录配置**
   - 确认记录类型是 `CNAME`
   - 确认记录值正确
   - 确认主机记录正确

2. **等待DNS生效**
   - 通常10分钟-2小时
   - 可以设置较短的TTL加速生效

3. **联系域名服务商**
   - 如果DNS配置正确但仍不生效
   - 可以联系域名服务商技术支持

### 如果域名无法访问
1. **检查API网关配置**
   - 确认域名已绑定
   - 确认SSL证书已绑定
   - 确认路径映射正确

2. **检查云函数状态**
   - 确认云函数正常运行
   - 查看云函数日志
   - 确认环境变量配置正确

---

## 🎯 总结

### 确认域名解析的步骤
1. ✅ 获取API网关的CNAME地址
2. ✅ 在DNS管理中添加CNAME记录
3. ✅ 使用 `nslookup` 或 `dig` 验证解析
4. ✅ 测试HTTPS访问
5. ✅ 测试API接口

### 验证成功的标志
- ✅ DNS查询返回API网关CNAME地址
- ✅ 可以通过HTTPS访问域名
- ✅ 健康检查接口返回正常
- ✅ API接口可以正常访问
- ✅ SSL证书有效

**完成以上步骤后，域名解析就配置成功了！** 🎉
