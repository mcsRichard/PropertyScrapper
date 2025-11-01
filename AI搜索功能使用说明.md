# AI对话搜索功能使用说明

## 功能概述

小程序前端搜索功能已升级为AI式对话搜索。用户可以用自然语言输入搜索条件（如"帝国理工大学附近2室一厅公寓4000镑以下"），系统会自动调用AI将查询翻译成具体的search filter，然后返回搜索结果。

## 实现的功能模块

### 1. 后端部分

#### 1.1 AI解析器 (`backend/utils/ai_parser.py`)
- **功能**: 将自然语言查询转换为结构化的筛选参数
- **支持三种解析方式**:
  - **DeepSeek API解析**（推荐，默认）: 使用DeepSeek API进行智能解析，国内更稳定，价格更低
  - **OpenAI API解析**（可选）: 使用OpenAI API进行智能解析
  - **正则解析**（备用）: 当AI服务不可用时，使用正则表达式作为备用方案

#### 1.2 API端点 (`backend/api/properties.py`)
- **新增端点**: `POST /api/properties/ai-search`
- **请求参数**:
  - `query`: 自然语言查询字符串（必需）
  - `listing_type`: 默认listing_type，'for_sale'或'for_rent'（可选，默认'for_rent'）
  - `page`: 页码（可选，默认1）
  - `limit`: 每页数量（可选，默认20）
- **返回数据**:
  - `properties`: 房产列表
  - `pagination`: 分页信息
  - `filters`: AI解析出的筛选条件（供前端显示）
  - `query`: 原始查询字符串

#### 1.3 配置文件 (`backend/config.py`)
- 新增AI搜索相关配置项：
  - `AI_API_TYPE`: API类型选择（'deepseek'或'openai'，默认'deepseek'）
  - `DEEPSEEK_API_KEY`: DeepSeek API密钥（推荐）
  - `OPENAI_API_KEY`: OpenAI API密钥（可选）

### 2. 前端部分

#### 2.1 API工具类 (`miniprogram/utils/api.js`)
- **新增方法**: `aiSearchProperties(query, listingType, page, limit)`
- 用于调用后端AI搜索API

#### 2.2 页面逻辑 (`miniprogram/pages/index/index.js`)
- **新增数据字段**:
  - `searchKeyword`: 搜索关键词
  - `aiFilters`: AI解析的筛选条件
  - `aiFiltersText`: AI筛选条件显示文本
- **新增方法**:
  - `onAISearch()`: AI对话式搜索
  - `formatAIFilters()`: 格式化AI筛选条件显示文本

#### 2.3 页面模板 (`miniprogram/pages/index/index.wxml`)
- 搜索框提示文本更新为："例如：帝国理工大学附近2室一厅公寓4000镑以下"
- 搜索按钮文本改为"AI搜索"
- 新增AI解析结果提示区域，显示解析出的筛选条件

#### 2.4 页面样式 (`miniprogram/pages/index/index.wxss`)
- 新增 `.ai-filter-tip` 样式，用于显示AI筛选提示

## 配置步骤

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

新增依赖：
- `openai==1.12.0` （DeepSeek与OpenAI使用相同的SDK，完全兼容）

### 2. 配置AI API密钥（推荐使用DeepSeek）

在 `backend/.env` 文件中添加：

```env
# 使用DeepSeek（推荐，国内更稳定，价格更低）
AI_API_TYPE=deepseek
DEEPSEEK_API_KEY=your-deepseek-api-key-here

# 或使用OpenAI（可选）
AI_API_TYPE=openai
OPENAI_API_KEY=your-openai-api-key-here
```

**获取DeepSeek API密钥**（推荐）:
1. 访问 https://platform.deepseek.com/
2. 注册/登录账号（支持国内手机号）
3. 进入 API Keys 页面
4. 创建新的API密钥
5. 复制密钥到 `.env` 文件
6. **价格优势**: DeepSeek API价格仅为OpenAI的约1/10-1/50，非常适合国内用户

**获取OpenAI API密钥**（可选）:
1. 访问 https://platform.openai.com/
2. 注册/登录账号（需要国外网络和支付方式）
3. 进入 API Keys 页面
4. 创建新的API密钥
5. 复制密钥到 `.env` 文件

**价格对比**（2024年参考）:
- **DeepSeek Chat**: 
  - 输入: ¥0.00014/1K tokens（约$0.00002）
  - 输出: ¥0.00056/1K tokens（约$0.00008）
  - 平均每次查询（约200 tokens）: ¥0.00014（约¥0.01/次）
  
- **OpenAI GPT-4o-mini**:
  - 输入: $0.15/1M tokens
  - 输出: $0.60/1M tokens
  - 平均每次查询（约200 tokens）: $0.00018（约$0.001/次）

**结论**: DeepSeek价格约为OpenAI的**1/5到1/10**，且国内访问更稳定，强烈推荐使用DeepSeek。

**注意**: 
- 如果未配置任何API密钥，系统会自动使用正则表达式作为备用解析方案
- 备用方案准确度较低，建议配置API密钥以获得最佳体验
- 默认使用DeepSeek，无需特殊配置

### 3. 重启API服务器

配置完成后，重启后端API服务器使配置生效。

## 使用示例

### 用户输入示例

1. **基础查询**:
   - "帝国理工大学附近2室一厅公寓4000镑以下"
   - 解析结果: 出租 · 帝国理工大学附近 · 2室 · 公寓 · £4000/月以下

2. **包含出售类型**:
   - "伦敦市中心3室别墅，价格50万到100万"
   - 解析结果: 出售 · 伦敦 · 3室 · 别墅 · £50.0万-£100.0万

3. **简单查询**:
   - "2室公寓"
   - 解析结果: 2室 · 公寓

### API调用示例

```javascript
// 小程序前端调用
const api = require('../../utils/api.js')

api.aiSearchProperties(
  '帝国理工大学附近2室一厅公寓4000镑以下',
  'for_rent',
  1,
  20
).then(res => {
  console.log('搜索结果:', res.data.properties)
  console.log('解析的筛选条件:', res.data.filters)
})
```

```bash
# 使用curl测试API
curl -X POST "http://localhost:5000/api/properties/ai-search?page=1&limit=20" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "帝国理工大学附近2室一厅公寓4000镑以下",
    "listing_type": "for_rent"
  }'
```

## AI解析支持的查询类型

### 1. 位置信息
- "帝国理工大学附近"
- "伦敦市中心"
- "牛津大学周边"
- "曼彻斯特"

### 2. 房间数量
- "1室"、"2室"、"3室"、"4室"、"5室"
- "1 bed"、"2 bedrooms"、"3 bed"
- "一室一厅"、"两室"

### 3. 房产类型
- "公寓" / "flat" / "apartment"
- "别墅" / "house"
- "单间" / "studio"

### 4. 价格范围
- "4000镑以下" / "少于4000镑"
- "4000-6000镑"
- "50万以上" / "超过50万"
- "30万到100万"

### 5. 出售/出租类型
- "出售" / "for_sale" / "sale"
- "出租" / "for_rent" / "rent" / "租"

## 注意事项

1. **API费用**: 
   - DeepSeek API按使用量收费，价格非常便宜（约¥0.01/次查询）
   - OpenAI API价格较高（约$0.001/次查询）
   - 建议使用DeepSeek以降低成本
   
2. **网络要求**: 
   - DeepSeek: 国内可直接访问，无需特殊网络配置
   - OpenAI: 需要服务器可以访问OpenAI服务器（可能需要代理）
   
3. **备用方案**: 如果AI服务不可用，系统会自动降级到正则表达式解析

4. **查询语言**: 支持中文和英文混合查询

5. **错误处理**: 前端已添加loading状态和错误提示，提升用户体验

6. **切换API**: 通过设置 `AI_API_TYPE=deepseek` 或 `AI_API_TYPE=openai` 可以切换不同的API提供商

## 文件清单

### 新增文件
- `backend/utils/ai_parser.py` - AI解析器

### 修改文件
- `backend/api/properties.py` - 添加AI搜索端点
- `backend/config.py` - 添加OpenAI配置
- `backend/requirements.txt` - 添加openai依赖
- `miniprogram/utils/api.js` - 添加AI搜索API方法
- `miniprogram/pages/index/index.js` - 添加AI搜索逻辑
- `miniprogram/pages/index/index.wxml` - 更新搜索UI
- `miniprogram/pages/index/index.wxss` - 添加AI提示样式

## 测试建议

1. **测试AI解析功能**:
   - 输入各种自然语言查询
   - 验证解析结果是否正确
   - 检查筛选条件是否准确

2. **测试备用方案**:
   - 临时移除OPENAI_API_KEY
   - 验证正则解析是否正常工作

3. **测试边界情况**:
   - 空查询
   - 模糊查询
   - 无效查询

4. **性能测试**:
   - 测试API响应时间
   - 检查是否有超时情况

