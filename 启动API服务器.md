# 启动API服务器

## 问题已解决

✅ SQLAlchemy兼容性问题已解决 - 已升级到2.0.35版本

## 启动方式

### 方法1：使用新脚本启动（推荐）

```bash
python start_api.py
```

### 方法2：传统方式启动

```bash
cd backend
python app.py
```

## 验证服务器启动成功

启动后，应该看到类似输出：

```
 * Running on http://0.0.0.0:5000
 * Debug mode: on
```

如果看到错误，请检查：

1. **端口5000是否被占用**
   ```bash
   netstat -ano | findstr :5000
   ```

2. **SQLAlchemy版本是否正确**
   ```bash
   pip show SQLAlchemy
   ```
   应该显示版本 2.0.35 或更高

## 启动后测试

在新的终端窗口运行：

```bash
python test_api_after_restart.py
```

或者使用curl：

```bash
# 测试出售房产（应该返回28个）
curl "http://localhost:5000/api/properties?listing_type=for_sale&limit=3"

# 测试出租房产（应该返回27个）
curl "http://localhost:5000/api/properties?listing_type=for_rent&limit=3"
```

## 预期结果

API应该返回正确的数据：

- `listing_type=for_sale` → 返回28个出售房产
- `listing_type=for_rent` → 返回27个出租房产

## 如果遇到问题

### 问题1：端口被占用

**错误**: `Address already in use`

**解决**：
```bash
# 找到占用端口的进程
netstat -ano | findstr :5000
# 结束进程（替换PID）
taskkill /PID <进程ID> /F
```

### 问题2：SQLAlchemy错误

**错误**: `AssertionError: Class <class 'sqlalchemy.sql.elements.SQLCoreOperations'> directly inherits TypingOnly`

**解决**：已经升级SQLAlchemy到2.0.35，应该不会出现这个错误

### 问题3：导入错误

**错误**: `ModuleNotFoundError: No module named 'config'`

**解决**：确保在正确的目录运行，使用 `python start_api.py` 而不是 `cd backend && python app.py`

## 完整启动流程

1. **确保SQLAlchemy已升级**（已完成）
2. **启动服务器**：
   ```bash
   python start_api.py
   ```
3. **等待服务器启动**（看到 "Running on" 提示）
4. **测试API**：
   ```bash
   python test_api_after_restart.py
   ```
5. **启动小程序并测试**

## 成功标志

启动成功后：

1. ✅ 终端显示 "Running on http://0.0.0.0:5000"
2. ✅ 测试脚本显示正确的数据类型和数量
3. ✅ API返回28个for_sale和27个for_rent
4. ✅ 小程序图片正常显示
5. ✅ 小程序切换"出售/出租"标签正常工作

