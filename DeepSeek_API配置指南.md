# DeepSeek API配置快速指南

## 为什么选择DeepSeek？

### 1. 价格优势（国内用户首选）

**DeepSeek Chat 定价**（2024年）:
- 输入: ¥0.00014/1K tokens（约$0.00002/1K tokens）
- 输出: ¥0.00056/1K tokens（约$0.00008/1K tokens）
- **平均每次查询成本**: 约¥0.01/次（查询约200 tokens）

**OpenAI GPT-4o-mini 定价**:
- 输入: $0.15/1M tokens = $0.00015/1K tokens
- 输出: $0.60/1M tokens = $0.0006/1K tokens
- **平均每次查询成本**: 约$0.00018/次（查询约200 tokens）

**价格对比**:
- DeepSeek约为OpenAI的 **1/5到1/10** 的价格
- 对于国内用户，使用人民币结算更便捷

### 2. 网络稳定性

- ✅ **DeepSeek**: 国内可直接访问，无需代理，延迟低，稳定性高
- ❌ **OpenAI**: 国内访问需要代理，可能存在网络不稳定问题

### 3. 使用便利性

- ✅ **DeepSeek**: 支持国内手机号注册，支付便捷
- ❌ **OpenAI**: 需要国外网络和支付方式（如信用卡），注册流程复杂

### 4. API兼容性

DeepSeek API与OpenAI API **完全兼容**，使用相同的SDK，代码无需修改即可切换。

## 快速配置步骤

### 1. 获取DeepSeek API密钥

1. 访问 **https://platform.deepseek.com/**
2. 点击"注册"或"登录"
   - 支持国内手机号注册
   - 也支持邮箱注册
3. 登录后，点击左侧菜单 "API Keys"
4. 点击"创建新密钥"或"Create API Key"
5. 输入密钥名称（如"房产搜索"）
6. 复制生成的API密钥（**注意：只显示一次，请妥善保存**）

### 2. 配置环境变量

在 `backend/.env` 文件中添加：

```env
# AI搜索功能配置
AI_API_TYPE=deepseek
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx  # 替换为你的实际密钥
```

### 3. 重启服务器

配置完成后，重启后端API服务器：

```bash
# 如果使用systemd
sudo systemctl restart your-api-service

# 或者如果直接运行
cd backend
python app.py
```

### 4. 验证配置

查看服务器日志，应该能看到：

```
[INFO] Using DEEPSEEK API for AI parsing
```

如果看到这个信息，说明配置成功！

## 成本估算

假设每天有 **1000次搜索查询**：

- **DeepSeek**: 1000次 × ¥0.01 = **¥10/天** = **¥300/月**
- **OpenAI**: 1000次 × $0.00018 × 7.2（汇率）≈ **¥1.3/天** = **¥39/月**

**注意**: 虽然单次查询OpenAI看似更便宜，但考虑到：
1. OpenAI需要代理服务成本
2. 网络不稳定导致的额外重试成本
3. 支付和汇率转换的复杂性

**实际使用中，DeepSeek的综合成本更低，且体验更好。**

## 常见问题

### Q: 可以使用OpenAI吗？

A: 可以。在 `.env` 文件中设置：
```env
AI_API_TYPE=openai
OPENAI_API_KEY=your-openai-key
```

### Q: DeepSeek的API稳定性如何？

A: DeepSeek是国产AI服务，在国内访问非常稳定，延迟通常在100-300ms，远低于需要代理的OpenAI。

### Q: 如何查看API使用量？

A: 登录 https://platform.deepseek.com/ ，在"使用统计"页面可以查看详细的API调用次数和费用。

### Q: 有免费额度吗？

A: DeepSeek通常为新用户提供一定的免费额度，具体请查看官网公告。

### Q: API密钥泄露了怎么办？

A: 立即登录DeepSeek平台，删除旧的API密钥，创建新密钥。请勿将API密钥提交到Git仓库。

## 切换到OpenAI（如果需要）

如果你需要使用OpenAI API，只需修改 `.env` 文件：

```env
# 切换为OpenAI
AI_API_TYPE=openai
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
DEEPSEEK_API_KEY=  # 可以留空或删除
```

重启服务器即可。代码会自动切换到OpenAI API。

## 技术支持

如有问题，可以：
1. 查看 `AI搜索功能使用说明.md` 了解详细配置
2. 查看服务器日志排查问题
3. 访问 DeepSeek官方文档: https://platform.deepseek.com/docs

