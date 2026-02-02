# 函数URL自定义域名配置步骤

## 📊 当前配置信息

**云函数URL**（已配置）：
```
公网HTTPS：https://1383789184-lebyqyy34m.ap-shanghai.tencentscf.com
```

**当前配置状态**：
- ✅ 函数URL已启用
- ❌ CORS未开启（需要开启）
- ❌ 自定义域名未配置（需要配置）

---

## 🎯 操作清单

### ✅ 第1步：开启CORS（必须！）

**在"触发管理"页面**：

1. 找到"CORS"配置项（当前显示"未开启"）
2. 点击"编辑"或"修改"按钮
3. 将CORS开关设置为"**开启**"
4. 保存配置

**CORS配置建议**（如果有详细选项）：
```
允许的源：*（或指定域名）
允许的方法：GET, POST, PUT, DELETE, OPTIONS
允许的头：*
允许凭证：是
```

**为什么必须开启**：
- 小程序访问API需要跨域支持
- 不开启CORS会导致请求被浏览器拦截
- 错误提示：`CORS policy: No 'Access-Control-Allow-Origin' header`

---

### ✅ 第2步：配置自定义域名

#### 2.1 进入自定义域名配置

**方法A：通过当前页面**
- 在"触发管理"页面查找是否有"自定义域名"选项
- 如果有，直接点击

**方法B：通过左侧菜单**
1. 在云函数控制台左侧菜单
2. 找到"函数管理" > "触发器"或"自定义域名"
3. 点击"自定义域名"

**方法C：直接访问**
- 链接：https://console.cloud.tencent.com/scf/custom-domain?rid=4
- 这是上海地域的自定义域名管理页面

#### 2.2 新建自定义域名

1. **点击"新建"或"绑定自定义域名"**

2. **填写域名配置**：

**基本信息**：
```
自定义域名：api.ukliving.cn
协议：HTTPS（推荐）或 HTTP & HTTPS
网络类型：公网
地域：ap-shanghai（上海）
```

**SSL证书**：
```
证书来源：腾讯云托管证书
选择证书：选择绑定域名为 api.ukliving.cn 的证书
```

⚠️ **重要**：
- 你有两个证书：
  - 证书1：`api.ukliving.cn` ✅ **选这个**
  - 证书2：`ukliving.cn`、`www.ukliving.cn` ❌ 不要选
- 必须选择域名匹配的证书

**路径映射**：
```
路径：/
函数：当前函数（应该自动选中）
版本/别名：$DEFAULT
```

**高级配置**：
```
启用CORS：是（勾选）
授权类型：开放
参数兼容：启用（如果有此选项）
```

3. **提交保存**
   - 点击"确定"或"提交"
   - 等待配置生效（通常3-5分钟）

#### 2.3 确认DNS记录

你的DNS记录已经配置正确（无需修改）：
```
类型：CNAME
主机记录：api
记录值：1383789184-lebyqyy34m.ap-shanghai.tencentscf.com
TTL：600
```

---

### ✅ 第3步：验证配置

#### 3.1 等待配置生效

配置提交后，等待**3-5分钟**让配置生效。

#### 3.2 测试健康检查接口

**在浏览器访问**：
```
https://api.ukliving.cn/health
```

**预期返回**：
```json
{
  "status": "healthy",
  "message": "Property API is running"
}
```

**检查SSL证书**：
- 点击浏览器地址栏的锁图标
- 查看证书信息
- 确认：
  - ✅ 证书域名：`api.ukliving.cn`
  - ✅ 证书有效
  - ✅ 浏览器显示绿色锁

#### 3.3 测试API接口

**在浏览器访问**：
```
https://api.ukliving.cn/api/properties?page=1&limit=10
```

**预期返回**：
- 房产列表JSON数据
- 没有CORS错误
- 响应状态200

#### 3.4 使用命令行测试（可选）

**Windows PowerShell**：
```powershell
# 测试健康检查
curl.exe https://api.ukliving.cn/health

# 测试API接口
curl.exe https://api.ukliving.cn/api/properties?page=1
```

---

## 🔍 配置界面参考

### 触发管理页面应该包含：

```
函数 URL
├── 访问路径
│   ├── 公网访问
│   │   ├── HTTPS: https://1383789184-lebyqyy34m.ap-shanghai.tencentscf.com
│   │   └── HTTP:  http://1383789184-lebyqyy34m.ap-shanghai.tencentscf.com
│   └── 内网访问
│       └── ...
├── CORS: 【未开启】 ← 需要点击编辑并开启
├── 授权类型: 开放
└── 参数兼容: 未启用
```

### 自定义域名配置页面：

```
新建自定义域名
├── 自定义域名: api.ukliving.cn
├── 协议: HTTPS ☑
├── SSL证书: [选择] api.ukliving.cn
├── 路径映射
│   ├── 路径: /
│   ├── 函数: [当前函数]
│   └── 版本: $DEFAULT
└── 高级配置
    ├── 启用CORS: ☑
    └── 授权类型: 开放
```

---

## ✅ 完成检查清单

### CORS配置
- [ ] 已在"触发管理"中开启CORS
- [ ] 保存配置成功

### 自定义域名配置
- [ ] 找到了自定义域名配置入口
- [ ] 创建了新的自定义域名绑定
- [ ] 域名：`api.ukliving.cn`
- [ ] 协议：HTTPS
- [ ] SSL证书：选择了 `api.ukliving.cn` 证书（正确的）
- [ ] 路径映射：`/` → 当前函数
- [ ] 高级配置：启用了CORS
- [ ] 提交保存成功

### DNS配置
- [ ] DNS记录类型：CNAME
- [ ] 主机记录：api
- [ ] 记录值：`1383789184-lebyqyy34m.ap-shanghai.tencentscf.com`
- [ ] 已生效（之前已确认）

### 访问测试
- [ ] 等待3-5分钟配置生效
- [ ] 可以访问：`https://api.ukliving.cn/health`
- [ ] 返回正确JSON数据
- [ ] SSL证书显示为 `api.ukliving.cn`
- [ ] 浏览器显示绿色锁
- [ ] API接口正常工作
- [ ] 没有CORS错误

---

## 🆘 常见问题

### Q1: 找不到"自定义域名"配置入口？

**可能位置**：
1. 云函数详情页 > 触发管理 > 自定义域名
2. 云函数控制台左侧菜单 > 自定义域名
3. 直接访问：https://console.cloud.tencent.com/scf/custom-domain?rid=4

**如果确实找不到**：
- 检查云函数地域是否正确（ap-shanghai）
- 尝试刷新页面
- 或联系腾讯云客服

### Q2: 没有看到CORS配置选项？

**可能情况**：
- CORS配置可能在"编辑"按钮里面
- 或在"高级配置"中
- 如果完全没有，可以在自定义域名配置时启用

**替代方案**：
- 在代码中配置CORS（Flask应用中已配置）
- 在自定义域名的高级配置中启用CORS

### Q3: 配置后仍然无法访问？

**检查步骤**：
1. 等待5-10分钟让配置完全生效
2. 清除浏览器缓存
3. 清除DNS缓存：`ipconfig /flushdns`（Windows）
4. 检查SSL证书是否选择正确
5. 查看云函数日志是否有错误
6. 确认CORS已启用

### Q4: SSL证书错误？

**检查**：
1. 确认选择的证书域名是 `api.ukliving.cn`
2. 确认证书状态为"已签发"
3. 如果选错了，修改配置重新选择

### Q5: CORS错误？

**错误信息**：
```
Access to fetch at 'https://api.ukliving.cn/...' has been blocked by CORS policy
```

**解决**：
1. 确认在触发管理中已开启CORS
2. 确认在自定义域名配置中已启用CORS
3. 检查Flask应用中的CORS配置（应该已配置）
4. 等待配置生效

---

## 📞 下一步

完成上述配置后，请告诉我：

1. **CORS是否已开启？**
   - [ ] 已开启
   - [ ] 找不到配置选项

2. **自定义域名是否配置成功？**
   - [ ] 已配置
   - [ ] 找不到配置入口
   - [ ] 配置失败（错误信息：_______）

3. **访问测试结果？**
   - [ ] 成功（可以访问 `https://api.ukliving.cn/health`）
   - [ ] 失败（错误信息：_______）

---

## 🎯 配置成功后的下一步

当自定义域名配置成功后，需要：

### 1. 更新微信小程序服务器域名

登录微信公众平台：https://mp.weixin.qq.com

配置以下域名：

**request合法域名**：
```
https://api.ukliving.cn
```

**downloadFile合法域名**：
```
https://api.ukliving.cn
https://[你的COS域名].cos.ap-shanghai.myqcloud.com
```

### 2. 测试小程序

1. 打开微信开发者工具
2. 编译小程序
3. 测试房产列表是否正常加载
4. 检查网络请求是否使用 `https://api.ukliving.cn`

### 3. 提交审核

所有功能测试正常后：
1. 上传小程序代码
2. 提交审核
3. 等待审核通过
4. 发布上线

---

## 🔗 相关链接

- **云函数控制台**：https://console.cloud.tencent.com/scf
- **自定义域名管理**：https://console.cloud.tencent.com/scf/custom-domain?rid=4
- **SSL证书管理**：https://console.cloud.tencent.com/ssl
- **DNS管理**：https://console.cloud.tencent.com/cns
- **微信公众平台**：https://mp.weixin.qq.com

---

## 💡 总结

**当前进度**：
1. ✅ 云函数运行正常
2. ✅ DNS解析配置正确
3. ✅ SSL证书已准备
4. 🔄 需要开启CORS
5. 🔄 需要配置自定义域名

**完成这两步后**，`https://api.ukliving.cn` 就可以正常使用了！

**预计时间**：10-15分钟（包括等待生效时间）

加油！🚀
