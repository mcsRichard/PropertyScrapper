# 如何验证AI搜索功能是否真的调用DeepSeek API

## 验证方法

### 方法1：查看服务器日志（最直接）

当AI搜索功能被调用时，服务器会输出详细的日志信息。查看日志可以确认：

1. **初始化日志**（服务器启动时）：
   ```
   [AI-PARSER] ✅ 初始化成功: 使用 DEEPSEEK API
   [AI-PARSER] 📍 API地址: https://api.deepseek.com
   [AI-PARSER] 🤖 模型: deepseek-chat
   [AI-PARSER] 🔑 API密钥: sk-xxxxxxxx...xxxx
   ```

2. **每次搜索时的日志**：
   ```
   [AI-SEARCH] ✅ 将使用 DEEPSEEK API 进行解析
   [AI-PARSER] 🚀 开始调用 DEEPSEEK API
   [AI-PARSER] 📍 请求地址: https://api.deepseek.com/chat/completions
   [AI-PARSER] 🤖 使用模型: deepseek-chat
   [AI-PARSER] ✅ API调用成功 (耗时: X.XX秒)
   [AI-PARSER] 📊 响应信息:
      - 模型: deepseek-chat
      - 使用tokens: XXX
      - 响应长度: XXX 字符
   ```

### 方法2：使用测试端点

访问测试端点查看配置状态：

**请求**：
```bash
GET http://your-server/api/properties/ai-test
```

**响应示例**（如果正确配置）：
```json
{
  "success": true,
  "data": {
    "ai_available": true,
    "api_type": "deepseek",
    "api_base": "https://api.deepseek.com",
    "model": "deepseek-chat",
    "api_key_configured": true,
    "sdk_available": true,
    "test_query": "帝国理工附近2室",
    "test_result": {
      "listing_type": "for_rent",
      "location": "imperial college",
      "bedrooms": 2
    },
    "test_success": true
  }
}
```

**如果未配置API密钥**：
```json
{
  "success": true,
  "data": {
    "ai_available": false,
    "api_type": "deepseek",
    "api_base": null,
    "model": null,
    "api_key_configured": false,
    "sdk_available": true
  }
}
```

### 方法3：检查环境变量

在服务器上检查环境变量：

```bash
# Linux/Mac
echo $AI_API_TYPE
echo $DEEPSEEK_API_KEY
echo $DEEPSEEK_API_BASE

# Windows PowerShell
$env:AI_API_TYPE
$env:DEEPSEEK_API_KEY
$env:DEEPSEEK_API_BASE
```

应该看到：
- `AI_API_TYPE=deepseek`（或未设置，默认就是deepseek）
- `DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxx`（你的实际密钥）
- `DEEPSEEK_API_BASE=https://api.deepseek.com`（或未设置，使用默认值）

### 方法4：网络抓包（高级）

如果服务器在本地或可以访问，可以使用网络抓包工具（如Wireshark、Charles）监控：

- **请求URL**: `https://api.deepseek.com/chat/completions`
- **请求头**: 包含 `Authorization: Bearer sk-xxxxxxxxxxxxx`
- **请求体**: 包含模型名称 `deepseek-chat`

### 方法5：查看DeepSeek平台使用统计

1. 登录 https://platform.deepseek.com/
2. 进入"使用统计"页面
3. 查看API调用记录
4. 如果看到调用记录，说明确实在使用DeepSeek API

## 如何判断是否真的在使用DeepSeek

### ✅ 确认使用的标志：

1. **日志显示**：
   - `[AI-PARSER] ✅ 初始化成功: 使用 DEEPSEEK API`
   - `[AI-PARSER] 📍 API地址: https://api.deepseek.com`
   - `[AI-PARSER] 🚀 开始调用 DEEPSEEK API`

2. **测试端点返回**：
   - `"api_type": "deepseek"`
   - `"api_base": "https://api.deepseek.com"`
   - `"ai_available": true`

3. **响应时间**：
   - DeepSeek API通常响应时间在0.5-2秒
   - 如果使用正则表达式降级，响应时间几乎为0

### ❌ 未使用DeepSeek的标志：

1. **日志显示**：
   - `[AI-PARSER] ⚠️ 警告: API密钥未配置，使用降级正则解析器`
   - `[AI-SEARCH] ⚠️ 将使用正则表达式降级解析（AI API不可用）`

2. **测试端点返回**：
   - `"ai_available": false`
   - `"api_key_configured": false`

## 常见问题排查

### Q: 日志显示"使用降级正则解析器"
**A**: 检查：
1. `DEEPSEEK_API_KEY` 环境变量是否设置
2. API密钥是否正确（以`sk-`开头）
3. 服务器是否重启以加载新的环境变量

### Q: 如何确认API真的被调用了？
**A**: 
1. 查看日志中的 `[AI-PARSER] ✅ API调用成功 (耗时: X.XX秒)` - 如果有耗时，说明真的调用了API
2. 查看DeepSeek平台的使用统计
3. 使用测试端点执行测试查询，查看返回结果

### Q: 如何切换回DeepSeek？
**A**: 
1. 设置环境变量：`AI_API_TYPE=deepseek`
2. 设置API密钥：`DEEPSEEK_API_KEY=your-key`
3. 重启服务器

## 快速验证命令

```bash
# 1. 测试API配置
curl http://localhost:5000/api/properties/ai-test

# 2. 执行一次AI搜索（查看日志）
curl -X POST http://localhost:5000/api/properties/ai-search \
  -H "Content-Type: application/json" \
  -d '{"query": "帝国理工附近2室", "listing_type": "for_rent"}'
```

查看服务器日志，应该看到详细的API调用信息。




