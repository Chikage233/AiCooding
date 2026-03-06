# Judge0 代码判题系统 API 接口文档

## 概述

本项目已集成 Judge0 代码判题系统，服务器部署在 `http://106.53.59.120:2358`。

## 接口列表

### 1. 获取支持的编程语言

**接口**: `GET /api/judge0/languages/`

**权限**: 公开 (无需认证)

**响应示例**:
```json
{
    "code": 200,
    "message": "获取语言列表成功",
    "data": {
        "languages": [
            {
                "id": 71,
                "name": "Python 3.8.1",
                "is_archived": false,
                "source_file": "script.py",
                "compile_cmd": null,
                "run_cmd": "/usr/local/python3.8.1/bin/python3 script.py"
            },
            {
                "id": 62,
                "name": "Java 11.0.6",
                "is_archived": false,
                "source_file": "Main.java",
                "compile_cmd": "/usr/local/openjdk11/bin/javac -d /tmp Main.java",
                "run_cmd": "/usr/local/openjdk11/bin/java -cp /tmp Main"
            }
        ],
        "language_map": {
            "python3": 71,
            "java": 62,
            "cpp": 54,
            "c": 50
        },
        "language_names": {
            "71": "Python 3.8.1",
            "62": "Java 11.0.6",
            "54": "C++ (GCC 9.2.0)",
            "50": "C (GCC 9.2.0)"
        }
    }
}
```

---

### 2. 提交代码执行 (完整参数版本)

**接口**: `POST /api/judge0/submit/`

**权限**: 公开 (无需认证)

**请求参数**:
```json
{
    "source_code": "print('Hello World')",
    "language_id": 71,
    "stdin": "",
    "expected_output": "",
    "cpu_time_limit": 5.0,
    "memory_limit": 128000,
    "stack_limit": 64000,
    "max_processes_and_or_threads": 60,
    "enable_per_process_and_thread_time_limit": false,
    "enable_per_process_and_thread_memory_limit": false,
    "redirect_stderr_to_stdout": false,
    "compiler_options": "",
    "command_line_arguments": "",
    "number_of_runs": 1
}
```

**参数说明**:
- `source_code` (必需): 源代码字符串
- `language_id` (必需): 编程语言 ID (从 languages 接口获取)
- `stdin` (可选): 标准输入
- `expected_output` (可选): 期望输出 (用于判断答案是否正确)
- `cpu_time_limit` (可选): CPU 时间限制，默认 5.0 秒
- `memory_limit` (可选): 内存限制，默认 128000 KB
- `stack_limit` (可选): 栈限制，默认 64000 KB
- `max_processes_and_or_threads` (可选): 最大进程/线程数，默认 60
- `enable_per_process_and_thread_time_limit` (可选): 是否启用每个进程/线程的时间限制，默认 false
- `enable_per_process_and_thread_memory_limit` (可选): 是否启用每个进程/线程的内存限制，默认 false
- `redirect_stderr_to_stdout` (可选): 是否将标准错误重定向到标准输出，默认 false
- `compiler_options` (可选): 编译器选项
- `command_line_arguments` (可选): 命令行参数
- `number_of_runs` (可选): 运行次数，默认 1

**响应示例**:
```json
{
    "code": 200,
    "message": "代码执行成功",
    "data": {
        "token": "abc123def456",
        "status": {
            "id": 3,
            "description": "Accepted"
        },
        "stdout": "Hello World\n",
        "stderr": null,
        "compile_output": null,
        "message": null,
        "exit_code": 0,
        "exit_signal": null,
        "time": 0.023,
        "wall_time": 0.156,
        "memory": 9216,
        "created_at": "2026-03-06T10:00:00.000Z",
        "finished_at": "2026-03-06T10:00:00.156Z"
    }
}
```

**状态码说明**:
- 1: In Queue (排队中)
- 2: Processing (执行中)
- 3: Accepted (通过)
- 4: Wrong Answer (答案错误)
- 5: Time Limit Exceeded (超时)
- 6: Compilation Error (编译错误)
- 7: Runtime Error (运行时错误)
- 8: Signal (信号)
- 9: Memory Limit Exceeded (内存超限)
- 10: Output Limit Exceeded (输出超限)
- 11: Presentation Error (格式错误)
- 12: Internal Error (系统错误)
- 13: Execution Format Error (执行格式错误)

---

### 3. 快速运行代码 (简化版)

**接口**: `POST /api/judge0/run/`

**权限**: 公开 (无需认证)

**说明**: 简化版接口，只需提供源代码和语言名称即可

**请求参数**:
```json
{
    "source_code": "print('Hello World')",
    "language": "python3",
    "stdin": ""
}
```

**支持的语言名称**:
- `python3` / `python`: Python 3.8.1
- `java`: Java 11.0.6
- `cpp`: C++ (GCC 9.2.0)
- `c`: C (GCC 9.2.0)
- `javascript`: JavaScript (Node.js 12.14.0)
- `go`: Go 1.13.5
- `rust`: Rust 1.40.0
- `csharp`: C# (Mono 6.6.0.161)
- `php`: PHP 7.4.1
- `ruby`: Ruby 2.7.0
- `swift`: Swift 5.2.3
- `kotlin`: Kotlin 1.3.70
- `scala`: Scala 2.13.2
- `typescript`: TypeScript 3.7.4

**响应示例**: 同完整版本接口

---

### 4. 批量提交代码

**接口**: `POST /api/judge0/batch-submit/`

**权限**: 公开 (无需认证)

**请求参数**:
```json
{
    "submissions": [
        {
            "source_code": "print('Test 1')",
            "language_id": 71
        },
        {
            "source_code": "#include <iostream>\nint main() { std::cout << \"Test 2\"; return 0; }",
            "language_id": 54
        }
    ],
    "wait": true
}
```

**参数说明**:
- `submissions` (必需): 提交列表，最多支持 20 个代码
- `wait` (可选): 是否等待结果，默认 true

**响应示例**:
```json
{
    "code": 200,
    "message": "批量提交成功",
    "data": {
        "results": [
            {
                "token": "token1",
                "status": {"id": 3, "description": "Accepted"},
                "stdout": "Test 1\n",
                "stderr": null,
                "compile_output": null,
                "time": 0.015,
                "memory": 3200
            },
            {
                "token": "token2",
                "status": {"id": 3, "description": "Accepted"},
                "stdout": "Test 2",
                "stderr": null,
                "compile_output": null,
                "time": 0.008,
                "memory": 4500
            }
        ],
        "count": 2
    }
}
```

---

### 5. 获取提交详情

**接口**: `GET /api/judge0/submission/<token>/`

**权限**: 公开 (无需认证)

**参数**:
- `token`: 提交令牌 (从 submit 接口返回)

**查询参数**:
- `fields`: 指定返回字段，逗号分隔，如 `stdout,time,memory`

**响应示例**: 同 submit 接口

---

### 6. 获取系统信息

**接口**: `GET /api/judge0/system-info/`

**权限**: 公开 (无需认证)

**响应示例**:
```json
{
    "code": 200,
    "message": "获取系统信息成功",
    "data": {
        "cpu_info": "Intel(R) Xeon(R) CPU E5-2630 v4 @ 2.20GHz",
        "cpu_count": 10,
        "memory_info": "16GB",
        "disk_info": "500GB",
        "judge0_version": "1.13.0"
    }
}
```

---

### 7. 健康检查

**接口**: `GET /api/judge0/health/`

**权限**: 公开 (无需认证)

**响应示例**:
```json
{
    "code": 200,
    "message": "Judge0 服务运行正常",
    "data": {
        "status": "healthy"
    }
}
```

---

## 使用示例

### Python 示例

```python
import requests

# 1. 快速运行 Python 代码
response = requests.post('http://your-api-url/api/judge0/run/', json={
    'source_code': 'print("Hello World")',
    'language': 'python3'
})

result = response.json()
if result['code'] == 200:
    print("输出:", result['data']['stdout'])
    print("执行时间:", result['data']['time'], '秒')
    print("内存使用:", result['data']['memory'], 'KB')

# 2. 提交 C++ 代码
cpp_code = """
#include <iostream>
using namespace std;

int main() {
    int a, b;
    cin >> a >> b;
    cout << a + b << endl;
    return 0;
}
"""

response = requests.post('http://your-api-url/api/judge0/submit/', json={
    'source_code': cpp_code,
    'language_id': 54,  # C++
    'stdin': '10 20',
    'expected_output': '30'
})

result = response.json()
if result['data']['status']['id'] == 3:
    print("答案正确!")
    print("输出:", result['data']['stdout'])
elif result['data']['status']['id'] == 4:
    print("答案错误!")
    print("期望输出:", result['data']['expected_output'])
    print("实际输出:", result['data']['stdout'])
```

### JavaScript 示例

```javascript
// 快速运行代码
async function runCode(sourceCode, language) {
    const response = await fetch('/api/judge0/run/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            source_code: sourceCode,
            language: language,
            stdin: ''
        })
    });
    
    const result = await response.json();
    
    if (result.code === 200) {
        console.log('输出:', result.data.stdout);
        console.log('执行时间:', result.data.time, '秒');
        console.log('内存使用:', result.data.memory, 'KB');
    }
    
    return result;
}

// 使用示例
runCode('print("Hello from Python!")', 'python3');
```

---

## 注意事项

1. **执行限制**: 
   - 默认 CPU 时间限制：5 秒
   - 默认内存限制：128MB
   - 可根据需要调整，但有上限

2. **安全考虑**:
   - 代码在隔离环境中运行
   - 无法访问网络
   - 文件系统访问受限

3. **性能优化**:
   - 使用 `batch-submit` 接口批量提交代码
   - 设置合理的 `wait` 参数避免长时间等待
   - 对于实时性要求不高的场景，可以异步获取结果

4. **错误处理**:
   - 检查返回的 `status.id` 判断执行状态
   - 编译错误查看 `compile_output`
   - 运行时错误查看 `stderr`

---

## 测试

运行测试脚本验证功能:

```bash
python test_judge0.py
```

测试内容包括:
- ✅ 健康检查
- ✅ 获取语言列表
- ✅ Python 代码执行
- ✅ C++ 代码执行
- ✅ Java 代码执行
- ✅ 带输入的代码执行
- ✅ 系统信息查询

---

## 配置说明

在 `AiCooding/settings.py` 中配置:

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

---

## 相关文件

- **客户端封装**: `api/judge0_client.py`
- **API 视图**: `api/judge0_views.py`
- **序列化器**: `api/serializers.py` (Judge0 相关部分)
- **URL 路由**: `api/urls.py` (Judge0 相关路由)
- **测试脚本**: `test_judge0.py`
