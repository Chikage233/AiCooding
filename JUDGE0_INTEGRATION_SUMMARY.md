# Judge0 代码判题系统集成总结

## 📋 项目概述

已成功在 Django 项目中集成 Judge0 代码判题系统，服务器部署地址：`http://106.53.59.120:2358`

## 📁 创建的文件

### 核心文件

1. **`api/judge0_client.py`** (357 行)
   - Judge0 API 客户端封装
   - 支持的语言映射
   - 代码提交、查询、批量提交功能
   - 健康检查和系统信息查询

2. **`api/judge0_views.py`** (313 行)
   - RESTful API 视图
   - 7 个接口端点
   - 完整的错误处理
   - 日志记录

3. **`api/serializers.py`** (新增 102 行)
   - CodeSubmissionSerializer
   - CodeSubmissionResponseSerializer
   - LanguageInfoSerializer
   - BatchSubmissionSerializer
   - SystemInfoSerializer

4. **`api/urls.py`** (新增 16 行)
   - 7 个 Judge0 路由配置

### 配置文件

5. **`AiCooding/settings.py`** (新增 14 行)
   - Judge0 基础 URL 配置
   - 执行限制配置
   - API Key 配置（可选）

### 测试和示例

6. **`test_judge0.py`** (351 行)
   - 7 个自动化测试用例
   - 覆盖所有主要功能
   - 包含 Python/C++/Java示例

7. **`judge0_examples.py`** (379 行)
   - 实际使用场景示例
   - LeetCode 风格判题
   - 性能对比测试
   - 异步提交示例

### 文档

8. **`JUDGE0_API_DOC.md`** (444 行)
   - 完整的 API 文档
   - 请求/响应示例
   - 状态码说明
   - 使用注意事项

9. **`FRONTEND_INTEGRATION_GUIDE.md`** (493 行)
   - 前端集成指南
   - JavaScript/React/Vue示例
   - 常用工具函数
   - 最佳实践

## 🚀 API 接口列表

| 接口 | 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|------|
| 语言列表 | GET | `/api/judge0/languages/` | 公开 | 获取支持的编程语言 |
| 提交代码 | POST | `/api/judge0/submit/` | 公开 | 完整参数版本 |
| 快速运行 | POST | `/api/judge0/run/` | 公开 | 简化版本 |
| 批量提交 | POST | `/api/judge0/batch-submit/` | 公开 | 最多 20 个代码 |
| 提交详情 | GET | `/api/judge0/submission/<token>/` | 公开 | 查询执行结果 |
| 系统信息 | GET | `/api/judge0/system-info/` | 公开 | 服务器信息 |
| 健康检查 | GET | `/api/judge0/health/` | 公开 | 服务状态检查 |

## 💻 支持的开发语言

- **Python 3.8.1** (ID: 71)
- **Java 11.0.6** (ID: 62)
- **C++ (GCC 9.2.0)** (ID: 54)
- **C (GCC 9.2.0)** (ID: 50)
- **JavaScript (Node.js 12.14.0)** (ID: 63)
- **Go 1.13.5** (ID: 60)
- **Rust 1.40.0** (ID: 73)
- **C# (Mono 6.6.0.161)** (ID: 51)
- **PHP 7.4.1** (ID: 68)
- **Ruby 2.7.0** (ID: 72)
- **Swift 5.2.3** (ID: 74)
- **Kotlin 1.3.70** (ID: 78)
- **Scala 2.13.2** (ID: 81)
- **TypeScript 3.7.4** (ID: 75)

## 🔧 配置说明

### settings.py 配置

```python
# Judge0 API 基础 URL
JUDGE0_BASE_URL = 'http://106.53.59.120:2358'

# Judge0 API Key (如果启用了认证)
# JUDGE0_API_KEY = 'your-api-key-here'

# 默认执行限制
JUDGE0_CPU_TIME_LIMIT = 5.0  # CPU 时间限制 (秒)
JUDGE0_MEMORY_LIMIT = 128000  # 内存限制 (KB)
JUDGE0_STACK_LIMIT = 64000  # 栈限制 (KB)
JUDGE0_MAX_PROCESSES = 60  # 最大进程/线程数
```

## 📊 使用示例

### 最简单的用法

```python
from api.judge0_client import judge0_client

# 提交 Python 代码
result = judge0_client.submit_and_wait(
    source_code='print("Hello World")',
    language_id=71,
    timeout=10
)

print(result['stdout'])  # Hello World
print(result['time'])    # 执行时间
print(result['memory'])  # 内存使用
```

### 前端调用示例

```javascript
// 快速运行代码
const response = await fetch('/api/judge0/run/', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        source_code: 'print("Hello")',
        language: 'python3'
    })
});

const result = await response.json();
console.log(result.data.stdout);
```

## ✅ 测试验证

运行测试脚本:

```bash
python test_judge0.py
```

测试覆盖:
- ✅ 健康检查
- ✅ 获取语言列表
- ✅ Python 代码执行
- ✅ C++ 代码执行
- ✅ Java 代码执行
- ✅ 带输入的代码执行
- ✅ 系统信息查询

## 📝 典型应用场景

### 1. LeetCode 风格在线判题

```python
def judge_solution(user_code, test_cases):
    results = []
    for test_case in test_cases:
        result = judge0_client.submit_and_wait(
            source_code=user_code,
            language_id=71,
            stdin=test_case['input'],
            expected_output=test_case['expected']
        )
        results.append(result['status']['id'] == 3)  # 判断是否通过
    return all(results)
```

### 2. 编程作业自动评分

```python
def grade_assignment(submissions):
    grades = []
    for submission in submissions:
        result = judge0_client.submit_and_wait(
            source_code=submission['code'],
            language_id=submission['language_id']
        )
        if result['status']['id'] == 3:
            grades.append(100)
        else:
            grades.append(0)
    return grades
```

### 3. 代码性能对比

```python
def benchmark_algorithms(algorithms):
    results = []
    for algo in algorithms:
        result = judge0_client.submit_and_wait(
            source_code=algo['code'],
            language_id=71
        )
        results.append({
            'name': algo['name'],
            'time': result['time'],
            'memory': result['memory']
        })
    return results
```

## 🔒 安全特性

- ✅ 代码在隔离环境中运行
- ✅ 无法访问外部网络
- ✅ 文件系统访问受限
- ✅ 可配置执行时间和内存限制
- ✅ 支持请求频率控制

## 📈 性能优化建议

1. **批量提交**: 使用 `batch-submit` 接口减少网络往返
2. **异步处理**: 对长时间运行的代码使用异步轮询
3. **缓存语言列表**: 语言列表已自动缓存 24 小时
4. **合理设置超时**: 根据代码类型设置合适的 timeout

## 🐛 常见问题

### Q1: 如何添加 API Key?

A: 在 settings.py 中取消注释并设置:
```python
JUDGE0_API_KEY = 'your-api-key-here'
```

### Q2: 如何调整执行限制?

A: 修改 settings.py 中的配置:
```python
JUDGE0_CPU_TIME_LIMIT = 10.0  # 增加到 10 秒
JUDGE0_MEMORY_LIMIT = 256000  # 增加到 256MB
```

### Q3: 如何处理编译错误？

A: 检查返回的 `compile_output` 字段:
```python
if result['status']['id'] == 6:
    print("编译错误:", result['compile_output'])
```

### Q4: 如何支持更多语言？

A: 在 `judge0_client.py` 的 `LANGUAGE_MAP` 中添加:
```python
LANGUAGE_MAP = {
    # ... existing languages ...
    'new_language': language_id
}
```

## 📚 相关资源

- [Judge0 官方文档](https://ce.judge0.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [LeetCode GraphQL API](./simple_test_scraper.py)

## 🎯 下一步工作

1. ✅ ~~Judge0 客户端封装~~
2. ✅ ~~RESTful API 接口~~
3. ✅ ~~序列化器和验证~~
4. ✅ ~~测试脚本~~
5. ✅ ~~文档编写~~
6. ⏳ 前端界面开发 (参考 FRONTEND_INTEGRATION_GUIDE.md)
7. ⏳ 与 LeetCode 题目集成
8. ⏳ 用户代码提交历史
9. ⏳ 自动判题系统
10. ⏳ 代码相似度检测

## 📞 技术支持

如有问题，请查看:
- 详细 API 文档：`JUDGE0_API_DOC.md`
- 前端集成指南：`FRONTEND_INTEGRATION_GUIDE.md`
- 使用示例：`judge0_examples.py`

---

**集成完成时间**: 2026-03-06  
**Judge0 服务器**: http://106.53.59.120:2358  
**Django 项目**: AiCooding
