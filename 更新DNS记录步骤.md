# 更新DNS记录步骤（用于自定义域名）

## 📊 需要更新的原因

配置自定义域名时，系统提示：
```
域名必须先添加CNAME记录，将域名指向函数的二级域名：
1383789184.ap-shanghai.tencentscf.com
```

### CNAME记录对比

| 用途 | CNAME值 | 说明 |
|------|---------|------|
| 函数URL直接访问 | `1383789184-lebyqyy34m.ap-shanghai.tencentscf.com` | 旧的，用于直接访问 |
| 自定义域名绑定 | `1383789184.ap-shanghai.tencentscf.com` | 新的，用于自定义域名 |

**需要将DNS记录从第一个改为第二个！**

---

## 🎯 操作步骤

### 步骤1：进入DNS管理

1. **访问腾讯云DNS控制台**
   - 链接：https://console.cloud.tencent.com/cns

2. **找到域名 `ukliving.cn`**
   - 在域名列表中找到
   - 点击"解析"按钮

---

### 步骤2：修改CNAME记录

1. **找到现有的CNAME记录**
   - 主机记录：`api`
   - 记录类型：`CNAME`
   - 当前记录值：`1383789184-lebyqyy34m.ap-shanghai.tencentscf.com`

2. **点击"修改"按钮**

3. **更新记录值**：

**删除旧值**：
```
1383789184-lebyqyy34m.ap-shanghai.tencentscf.com
```

**填写新值**：
```
1383789184.ap-shanghai.tencentscf.com
```

**完整配置**：
```
记录类型:   CNAME
主机记录:   api
记录值:     1383789184.ap-shanghai.tencentscf.com  ← 新的值
TTL:        600（保持不变）
```

4. **点击"保存"**

---

### 步骤3：等待DNS生效

#### 生效时间
- **最快**：10分钟（TTL为600秒）
- **通常**：10-30分钟
- **最长**：2小时（极少数情况）

#### 检查DNS是否生效

**Windows PowerShell**：
```powershell
# 清除DNS缓存
ipconfig /flushdns

# 检查CNAME记录
Resolve-DnsName api.ukliving.cn -Type CNAME
```

**预期结果**（DNS生效后）：
```
Name                           Type   TTL   Section    NameHost
----                           ----   ---   -------    --------
api.ukliving.cn                CNAME  600   Answer     1383789184.ap-shanghai.tencentscf.com
```

**Mac/Linux**：
```bash
# 检查CNAME记录
dig api.ukliving.cn CNAME

# 或
nslookup api.ukliving.cn
```

---

### 步骤4：返回自定义域名配置页面

DNS生效后：

1. **返回腾讯云自定义域名配置页面**
   - 链接：https://console.cloud.tencent.com/scf/custom-domain?rid=4

2. **重新点击"添加自定义域名"**

3. **填写配置**：
   ```
   域名:        api.ukliving.cn
   协议:        HTTPS
   SSL证书:     选择 api.ukliving.cn 的证书
   路径:        /
   函数:        选择你的函数
   版本:        $DEFAULT
   ```

4. **提交保存**

这次应该不会再提示CNAME错误了！

---

## 🔍 验证步骤

### 1. 验证DNS记录更新

**在线工具验证**：
- 访问：https://tool.chinaz.com/dns
- 输入：`api.ukliving.cn`
- 选择：CNAME记录
- 点击查询

**预期结果**：
```
CNAME记录：1383789184.ap-shanghai.tencentscf.com
```

### 2. 验证自定义域名配置

配置成功后，在"自定义域名"列表中应该看到：
```
域名:        api.ukliving.cn
状态:        已绑定
HTTPS:       已启用
SSL证书:     api.ukliving.cn
```

### 3. 验证访问

**浏览器测试**：
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
- 证书域名应该显示：`api.ukliving.cn`
- 浏览器显示绿色锁（安全连接）

---

## ⚠️ 常见问题

### Q1: DNS修改后多久生效？

**答**：
- TTL为600秒（10分钟），通常10-30分钟生效
- 可以使用 `ipconfig /flushdns` 清除本地DNS缓存
- 使用在线工具检查是否生效

### Q2: 修改DNS后，旧的函数URL还能用吗？

**答**：可以！
- 旧URL：`https://1383789184-lebyqyy34m.ap-shanghai.tencentscf.com`
- 新域名：`https://api.ukliving.cn`
- 两个都可以访问，互不影响

### Q3: 如果DNS已生效，但自定义域名配置仍报错？

**检查**：
1. 确认CNAME值完全正确（没有多余的空格或字符）
2. 等待完整的TTL时间（10分钟）
3. 清除浏览器缓存
4. 尝试使用在线DNS查询工具验证

### Q4: CNAME记录值结尾需要加点号吗？

**答**：
- 不需要！填写：`1383789184.ap-shanghai.tencentscf.com`
- 腾讯云DNS会自动处理
- 如果系统自动添加了点号（`1383789184.ap-shanghai.tencentscf.com.`），这是正常的

---

## ✅ 完成检查清单

### DNS记录更新
- [ ] 进入DNS管理控制台
- [ ] 找到 `api` 的CNAME记录
- [ ] 点击"修改"
- [ ] 更新记录值为：`1383789184.ap-shanghai.tencentscf.com`
- [ ] 保存修改

### 等待生效
- [ ] 等待10-30分钟
- [ ] 使用 `nslookup` 或在线工具检查
- [ ] 确认CNAME记录已更新

### 自定义域名配置
- [ ] 返回自定义域名配置页面
- [ ] 重新点击"添加自定义域名"
- [ ] 填写配置信息
- [ ] 提交保存（不再提示CNAME错误）

### 访问测试
- [ ] 访问 `https://api.ukliving.cn/health`
- [ ] 返回正确JSON数据
- [ ] SSL证书有效
- [ ] 浏览器显示绿色锁

---

## 📞 需要帮助？

完成DNS修改后，请告诉我：

1. **DNS记录是否已修改？**
   - [ ] 已修改（新值：1383789184.ap-shanghai.tencentscf.com）
   - [ ] 遇到问题（什么问题：_______）

2. **DNS是否已生效？**
   - [ ] 已生效（nslookup显示新的CNAME）
   - [ ] 还在等待
   - [ ] 不确定如何检查

3. **自定义域名配置是否成功？**
   - [ ] 成功（已添加到列表）
   - [ ] 仍然提示CNAME错误
   - [ ] 其他错误（错误信息：_______）

---

## 🎯 总结

**关键步骤**：
1. ✅ 修改DNS记录CNAME值
2. ⏳ 等待10-30分钟DNS生效
3. 🔄 返回配置页面重新提交
4. ✅ 配置成功后测试访问

**新的CNAME值**：
```
1383789184.ap-shanghai.tencentscf.com
```

完成这些步骤后，自定义域名就配置成功了！🎉
