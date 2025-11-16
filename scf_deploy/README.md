# 云函数部署包

## 📁 目录结构

```
scf_deploy/
├── index.py                      # 云函数入口文件
├── requirements.txt              # Python依赖文件
├── README.md                     # 本文件
├── 部署步骤详细说明.md            # 详细部署步骤
├── 环境变量配置清单.md            # 环境变量配置指南
└── backend/                      # 需要手动复制backend目录到这里
    ├── app.py
    ├── config.py
    ├── requirements.txt
    ├── api/
    ├── models/
    └── utils/
```

---

## 🚀 快速开始

### 步骤1：准备部署包

1. **复制backend目录**
   ```bash
   # 在项目根目录执行
   xcopy /E /I backend scf_deploy\backend
   ```
   或手动将 `backend` 目录复制到 `scf_deploy` 目录下

2. **确认文件结构**
   - ✅ `scf_deploy/index.py` 存在
   - ✅ `scf_deploy/requirements.txt` 存在
   - ✅ `scf_deploy/backend/` 目录存在
   - ✅ `scf_deploy/backend/app.py` 存在

### 步骤2：部署到云函数

按照 `部署步骤详细说明.md` 中的步骤操作：

1. **创建云函数**（Web函数）
2. **上传代码**（本地上传 `scf_deploy` 目录）
3. **配置环境变量**（参考 `环境变量配置清单.md`）
4. **配置HTTP触发器**
5. **测试部署**

---

## 📋 部署检查清单

### 部署前检查
- [ ] `index.py` 入口文件已准备
- [ ] `requirements.txt` 已准备
- [ ] `backend/` 目录已复制到 `scf_deploy/`
- [ ] 所有代码文件完整

### 部署后检查
- [ ] 云函数创建成功
- [ ] 代码上传成功
- [ ] 环境变量配置完成
- [ ] HTTP触发器配置完成
- [ ] 健康检查接口正常
- [ ] API接口测试通过

---

## 📖 详细文档

- **部署步骤**：查看 `部署步骤详细说明.md`
- **环境变量配置**：查看 `环境变量配置清单.md`
- **上线步骤**：查看项目根目录的 `小程序上线步骤清单.md`

---

## ⚠️ 重要提示

1. **不要上传 `.env` 文件**
   - 所有配置通过环境变量设置
   - `.env` 文件包含敏感信息，不要上传

2. **不要上传 `__pycache__` 目录**
   - 这些是Python缓存文件
   - 云函数会自动生成

3. **确保入口文件正确**
   - 入口文件：`index.py`
   - 入口函数：`app`（不是 `main_handler`）

4. **选择Web函数**
   - 必须是"Web函数"，不是"事件函数"
   - Web函数支持直接运行Flask应用

---

## 🆘 遇到问题？

1. 查看 `部署步骤详细说明.md` 中的"常见问题排查"
2. 查看云函数日志
3. 检查环境变量配置
4. 验证代码文件完整性

---

## 📞 相关文档

- 腾讯云SCF文档：https://cloud.tencent.com/document/product/583
- 云函数Web函数：https://cloud.tencent.com/document/product/583/56124
