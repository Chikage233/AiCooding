# Judge0 代码判题系统 - 快速开始指南

## 🎯 项目概述

本项目已完成 Judge0 代码判题系统的集成，提供完整的 RESTful API 供前端使用。

**服务器地址**: `http://106.53.59.120:2358`  
**API 端点**: `/api/judge0/...`

---

## ⚡ 5 分钟快速开始

### 1. 检查服务状态

```bash
# 运行健康检查
curl http://localhost:8000/api/judge0/health/
```

**预期响应**:
```json
{
    "code": 200,
    "message": "Judge0 服务运行正常",
    "data": {"status": "healthy"}
}
```

### 2. 获取支持的编程语言

```bash
curl http://localhost:8000/api/judge0/languages/
```

### 3. 运行第一行代码

```bash
curl -X POST http://localhost:8000/api/judge0/run/ \
  -H "Content-Type: application/json" \
  -d '{
    "source_code": "print(\"Hello World\")",
    "language": "python3"
  }'
```

**预期响应**:
```json
{
    "code": 200,
    "message": "代码执行完成",
    "data": {
        "stdout": "Hello World\n",
        "status": {"description": "Accepted"},
        "time": 0.017,
        "memory": 3272
    }
}
```

---

## 📚 核心接口

| 接口 | 说明 | 示例 |
|------|------|------|
| `GET /api/judge0/languages/` | 获取语言列表 | [查看](#1-获取语言列表) |
| `POST /api/judge0/run/` | 快速运行代码 | [查看](#2-快速运行代码) |
| `POST /api/judge0/submit/` | 完整参数提交 | [查看](#3-完整参数提交) |
| `GET /api/judge0/submission/<token>/` | 查询提交结果 | [查看](#4-查询结果) |
| `POST /api/judge0/batch-submit/` | 批量提交 | [查看](#5-批量提交) |

---

## 💻 常用示例

### 1. 获取语言列表

```javascript
// JavaScript
fetch('/api/judge0/languages/')
    .then(res => res.json())
    .then(data => console.log(data.data.languages));
```

```python
# Python
from api.judge0_client import judge0_client

languages = judge0_client.get_languages()
for lang in languages[:5]:
    print(f"{lang['id']}: {lang['name']}")
```

### 2. 快速运行代码

```javascript
// JavaScript
fetch('/api/judge0/run/', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        source_code: 'print("Hello Python!")',
        language: 'python3'
    })
})
.then(res => res.json())
.then(data => {
    console.log('输出:', data.data.stdout);
    console.log('时间:', data.data.time, '秒');
});
```

```python
# Python
from api.judge0_client import judge0_client

result = judge0_client.submit_and_wait(
    source_code='print("Hello Python!")',
    language_id=71  # Python 3.8.1
)

print(f"输出：{result['stdout']}")
print(f"时间：{result['time']}秒")
print(f"内存：{result['memory']}KB")
```

### 3. 完整参数提交

```javascript
// JavaScript
fetch('/api/judge0/submit/', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        source_code: `
            #include <iostream>
            using namespace std;
            int main() {
                int a, b;
                cin >> a >> b;
                cout << a + b << endl;
                return 0;
            }
        `,
        language_id: 54,  // C++
        stdin: "10 20",
        expected_output: "30"
    })
})
.then(res => res.json())
.then(data => {
    if (data.data.status.id === 3) {
        console.log('答案正确!');
    } else {
        console.log('状态:', data.data.status.description);
    }
});
```

### 4. 查询提交结果

```javascript
// 先提交获取 token
const submitRes = await fetch('/api/judge0/submit/', {...});
const submitData = await submitRes.json();
const token = submitData.data.token;

// 轮询结果
async function pollResult(token) {
    const maxAttempts = 20;
    for (let i = 0; i < maxAttempts; i++) {
        const res = await fetch(`/api/judge0/submission/${token}/`);
        const data = await res.json();
        
        if (data.data.status.id > 2) {
            console.log('最终结果:', data.data);
            return data.data;
        }
        
        await new Promise(r => setTimeout(r, 500));
    }
}

pollResult(token);
```

### 5. 批量提交

```javascript
// JavaScript
const submissions = [
    {source_code: 'print(1)', language_id: 71},
    {source_code: 'print(2)', language_id: 71},
    {source_code: 'print(3)', language_id: 71}
];

fetch('/api/judge0/batch-submit/', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        submissions: submissions,
        wait: true
    })
})
.then(res => res.json())
.then(data => {
    data.data.results.forEach((result, i) => {
        console.log(`代码${i+1}:`, result.stdout);
    });
});
```

---

## 🔧 配置说明

### settings.py

```python
# Judge0 API 基础 URL
JUDGE0_BASE_URL = 'http://106.53.59.120:2358'

# API Key (如果需要认证)
# JUDGE0_API_KEY = 'your-key-here'

# 默认限制
JUDGE0_CPU_TIME_LIMIT = 5.0      # 5 秒
JUDGE0_MEMORY_LIMIT = 128000     # 128MB
JUDGE0_STACK_LIMIT = 64000       # 64MB
JUDGE0_MAX_PROCESSES = 60        # 60 个进程
```

---

## 📊 支持的语言

| 语言 | ID | 版本 |
|------|----|----|
| Python 3 | 71 | 3.8.1 |
| Java | 62 | 11.0.6 |
| C++ | 54 | GCC 9.2.0 |
| C | 50 | GCC 9.2.0 |
| JavaScript | 63 | Node.js 12.14.0 |
| Go | 60 | 1.13.5 |
| Rust | 73 | 1.40.0 |
| C# | 51 | Mono 6.6.0.161 |
| PHP | 68 | 7.4.1 |
| Ruby | 72 | 2.7.0 |
| Swift | 74 | 5.2.3 |
| Kotlin | 78 | 1.3.70 |
| Scala | 81 | 2.13.2 |
| TypeScript | 75 | 3.7.4 |

---

## 🐛 常见问题

### Q1: 如何运行需要输入的程序？

**A**: 有三种方法:

```python
# 方法 1: 直接在代码中包含输入
code = """
inputs = ["a", "b", "c"]
for x in inputs:
    print(x)
"""

# 方法 2: 使用命令行参数
code = """
import sys
for arg in sys.argv[1:]:
    print(arg)
"""
result = judge0_client.submit_and_wait(
    source_code=code,
    language_id=71,
    command_line_arguments="arg1 arg2 arg3"
)

# 方法 3: Base64 编码的 stdin (如果服务器支持)
import base64
stdin_b64 = base64.b64encode(b"input1\ninput2").decode()
result = judge0_client.submit_and_wait(
    source_code=code,
    language_id=71,
    stdin=stdin_b64
)
```

### Q2: 如何处理编译错误？

**A**: 检查 `compile_output` 字段:

```python
if result['status']['id'] == 6:
    print("编译错误:")
    print(result['compile_output'])
```

### Q3: 如何判断答案是否正确？

**A**: 使用 `expected_output` 参数:

```python
result = judge0_client.submit_and_wait(
    source_code=user_code,
    language_id=71,
    stdin=test_input,
    expected_output=expected_result
)

if result['status']['id'] == 3:
    print("✅ 答案正确")
elif result['status']['id'] == 4:
    print("❌ 答案错误")
    print("期望:", expected_result)
    print("实际:", result['stdout'])
```

---

## 📖 详细文档

- **API 文档**: [`JUDGE0_API_DOC.md`](./JUDGE0_API_DOC.md)
- **前端集成**: [`FRONTEND_INTEGRATION_GUIDE.md`](./FRONTEND_INTEGRATION_GUIDE.md)
- **使用示例**: [`judge0_examples.py`](./judge0_examples.py)
- **集成总结**: [`JUDGE0_INTEGRATION_SUMMARY.md`](./JUDGE0_INTEGRATION_SUMMARY.md)

---

## ✅ 测试验证

运行自动化测试:

```bash
python test_judge0.py
```

当前状态: **85.7% 通过率** (6/7 测试通过)

---

## 🚀 下一步

1. **启动 Django 服务器**:
   ```bash
   python manage.py runserver
   ```

2. **访问 API**:
   - 浏览器打开：`http://localhost:8000/api/judge0/languages/`
   - 或使用 Postman/cURL 测试

3. **开发前端界面**:
   - 参考 [`FRONTEND_INTEGRATION_GUIDE.md`](./FRONTEND_INTEGRATION_GUIDE.md)
   - 使用提供的 React/Vue 组件示例

---

## 📞 技术支持

遇到问题请查阅:
1. 相关文档文件
2. 测试脚本 `test_judge0.py`
3. 示例代码 `judge0_examples.py`

---

**创建时间**: 2026-03-06  
**服务器**: http://106.53.59.120:2358  
**状态**: ✅ 正常运行  
**测试**: ✅ 6/7 通过
