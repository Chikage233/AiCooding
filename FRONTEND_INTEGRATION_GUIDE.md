# Judge0 前端集成指南

## 快速开始

### 1. 检查服务状态

```javascript
// 检查 Judge0 服务是否可用
async function checkJudge0Health() {
    const response = await fetch('/api/judge0/health/');
    const result = await response.json();
    
    if (result.code === 200) {
        console.log('✅ Judge0 服务正常运行');
        return true;
    } else {
        console.error('❌ Judge0 服务异常');
        return false;
    }
}
```

### 2. 获取支持的编程语言

```javascript
// 获取语言列表
async function getSupportedLanguages() {
    const response = await fetch('/api/judge0/languages/');
    const result = await response.json();
    
    if (result.code === 200) {
        // 显示语言选择下拉框
        const languages = result.data.languages;
        const languageMap = result.data.language_map;
        
        // 示例：填充下拉框
        const select = document.getElementById('languageSelect');
        for (const [name, id] of Object.entries(languageMap)) {
            const option = document.createElement('option');
            option.value = id;
            option.textContent = name;
            select.appendChild(option);
        }
        
        return languages;
    }
}
```

### 3. 快速运行代码

```javascript
// 最简单的代码执行方式
async function runCodeQuickly(sourceCode, language) {
    try {
        const response = await fetch('/api/judge0/run/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                source_code: sourceCode,
                language: language,  // 'python3', 'java', 'cpp' 等
                stdin: ''
            })
        });
        
        const result = await response.json();
        
        if (result.code === 200) {
            const data = result.data;
            
            // 显示结果
            console.log('输出:', data.stdout);
            console.log('执行时间:', data.time, '秒');
            console.log('内存使用:', data.memory, 'KB');
            console.log('状态:', data.status.description);
            
            return {
                success: true,
                output: data.stdout,
                error: data.stderr,
                status: data.status.description,
                time: data.time,
                memory: data.memory
            };
        } else {
            throw new Error(result.message);
        }
    } catch (error) {
        console.error('执行失败:', error);
        return {
            success: false,
            error: error.message
        };
    }
}

// 使用示例
runCodeQuickly('print("Hello World")', 'python3')
    .then(result => {
        if (result.success) {
            document.getElementById('output').textContent = result.output;
        }
    });
```

### 4. 完整参数的代码提交

```javascript
// 使用完整参数提交代码
async function submitCode(code, languageId, options = {}) {
    const defaultOptions = {
        cpu_time_limit: 5.0,
        memory_limit: 128000,
        stack_limit: 64000,
        max_processes_and_or_threads: 60,
        enable_per_process_and_thread_time_limit: false,
        enable_per_process_and_thread_memory_limit: false,
        redirect_stderr_to_stdout: false
    };
    
    const submitData = {
        source_code: code,
        language_id: languageId,
        ...defaultOptions,
        ...options
    };
    
    try {
        const response = await fetch('/api/judge0/submit/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(submitData)
        });
        
        const result = await response.json();
        
        if (result.code === 200 || result.code === 202) {
            return result.data;
        } else {
            throw new Error(result.message);
        }
    } catch (error) {
        console.error('提交失败:', error);
        return null;
    }
}
```

### 5. 批量提交代码

```javascript
// 批量测试多段代码
async function batchSubmitCode(submissions) {
    try {
        const response = await fetch('/api/judge0/batch-submit/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                submissions: submissions,  // 最多 20 个
                wait: true  // 等待所有代码执行完成
            })
        });
        
        const result = await response.json();
        
        if (result.code === 200) {
            return result.data.results;
        } else {
            throw new Error(result.message);
        }
    } catch (error) {
        console.error('批量提交失败:', error);
        return null;
    }
}

// 使用示例
const submissions = [
    {
        source_code: 'print("Test 1")',
        language_id: 71
    },
    {
        source_code: 'print("Test 2")',
        language_id: 71
    }
];

batchSubmitCode(submissions).then(results => {
    results.forEach((result, index) => {
        console.log(`代码${index + 1}:`, result.stdout);
    });
});
```

### 6. 轮询异步任务结果

```javascript
// 异步提交并轮询结果
async function submitAndPoll(sourceCode, languageId, onProgress) {
    // 第一步：提交代码
    const submitResponse = await fetch('/api/judge0/submit/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            source_code: sourceCode,
            language_id: languageId
        })
    });
    
    const submitResult = await submitResponse.json();
    const token = submitResult.data.token;
    
    // 第二步：轮询结果
    const maxAttempts = 40; // 最多轮询 40 次
    let attempts = 0;
    
    while (attempts < maxAttempts) {
        await new Promise(resolve => setTimeout(resolve, 500)); // 等待 500ms
        
        const detailResponse = await fetch(`/api/judge0/submission/${token}/`);
        const detailResult = await detailResponse.json();
        
        const statusId = detailResult.data.status.id;
        
        // 状态码 > 2 表示执行完成
        if (statusId > 2) {
            return detailResult.data;
        }
        
        // 进度回调
        if (onProgress) {
            onProgress(attempts, maxAttempts, statusId);
        }
        
        attempts++;
    }
    
    throw new Error('等待超时');
}

// 使用示例
submitAndPoll(code, 71, (current, total, statusId) => {
    console.log(`执行中... ${Math.round(current / total * 100)}%`);
}).then(result => {
    console.log('最终结果:', result);
});
```

### 7. React 组件示例

```jsx
import React, { useState, useEffect } from 'react';

function CodeExecutor() {
    const [code, setCode] = useState('print("Hello World")');
    const [language, setLanguage] = useState('python3');
    const [output, setOutput] = useState('');
    const [status, setStatus] = useState('');
    const [loading, setLoading] = useState(false);
    const [languages, setLanguages] = useState([]);

    // 加载支持的语言
    useEffect(() => {
        fetch('/api/judge0/languages/')
            .then(res => res.json())
            .then(data => {
                if (data.code === 200) {
                    setLanguages(data.data.languages);
                }
            });
    }, []);

    // 执行代码
    const executeCode = async () => {
        setLoading(true);
        setStatus('执行中...');
        
        try {
            const response = await fetch('/api/judge0/run/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    source_code: code,
                    language: language
                })
            });
            
            const result = await response.json();
            
            if (result.code === 200) {
                setOutput(result.data.stdout);
                setStatus(result.data.status.description);
            } else {
                setStatus('执行失败');
            }
        } catch (error) {
            setStatus('错误：' + error.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="code-executor">
            <h2>在线代码执行器</h2>
            
            <select 
                value={language} 
                onChange={(e) => setLanguage(e.target.value)}
            >
                {Object.entries({
                    'python3': 'Python',
                    'java': 'Java',
                    'cpp': 'C++',
                    'c': 'C',
                    'javascript': 'JavaScript'
                }).map(([key, name]) => (
                    <option key={key} value={key}>{name}</option>
                ))}
            </select>
            
            <textarea
                value={code}
                onChange={(e) => setCode(e.target.value)}
                rows="10"
                placeholder="输入代码..."
            />
            
            <button onClick={executeCode} disabled={loading}>
                {loading ? '执行中...' : '运行代码'}
            </button>
            
            {status && <div>状态：{status}</div>}
            {output && (
                <pre>
                    <h3>输出:</h3>
                    {output}
                </pre>
            )}
        </div>
    );
}

export default CodeExecutor;
```

### 8. Vue 组件示例

```vue
<template>
  <div class="code-runner">
    <h2>代码运行器</h2>
    
    <select v-model="selectedLanguage">
      <option value="python3">Python</option>
      <option value="java">Java</option>
      <option value="cpp">C++</option>
      <option value="javascript">JavaScript</option>
    </select>
    
    <codemirror
      v-model="code"
      :options="cmOptions"
    />
    
    <button @click="runCode" :disabled="loading">
      {{ loading ? '运行中...' : '运行代码' }}
    </button>
    
    <div v-if="result">
      <h3>执行结果</h3>
      <p>状态：{{ result.status }}</p>
      <pre>{{ result.output }}</pre>
      <p>时间：{{ result.time }}s | 内存：{{ result.memory }}KB</p>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      code: 'print("Hello Vue!")',
      selectedLanguage: 'python3',
      loading: false,
      result: null,
      cmOptions: {
        mode: 'text/x-python',
        theme: 'monokai'
      }
    };
  },
  methods: {
    async runCode() {
      this.loading = true;
      this.result = null;
      
      try {
        const response = await fetch('/api/judge0/run/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            source_code: this.code,
            language: this.selectedLanguage
          })
        });
        
        const data = await response.json();
        
        if (data.code === 200) {
          this.result = {
            status: data.data.status.description,
            output: data.data.stdout,
            time: data.data.time,
            memory: data.data.memory
          };
        }
      } catch (error) {
        alert('执行失败：' + error.message);
      } finally {
        this.loading = false;
      }
    }
  }
};
</script>
```

## 常用语言 ID 映射

```javascript
const LANGUAGE_MAP = {
    'python3': 71,
    'python': 71,
    'java': 62,
    'cpp': 54,
    'c': 50,
    'javascript': 63,
    'go': 60,
    'rust': 73,
    'csharp': 51,
    'php': 68,
    'ruby': 72,
    'swift': 74,
    'kotlin': 78,
    'scala': 81,
    'typescript': 75
};
```

## 状态码对照表

```javascript
const STATUS_MAP = {
    1: '排队中',
    2: '执行中',
    3: '通过 (Accepted)',
    4: '答案错误 (Wrong Answer)',
    5: '超时 (Time Limit Exceeded)',
    6: '编译错误 (Compilation Error)',
    7: '运行时错误 (Runtime Error)',
    8: '信号 (Signal)',
    9: '内存超限 (Memory Limit Exceeded)',
    10: '输出超限 (Output Limit Exceeded)',
    11: '格式错误 (Presentation Error)',
    12: '系统错误 (Internal Error)',
    13: '执行格式错误 (Execution Format Error)'
};
```

## 注意事项

1. **跨域问题**: 如果前端和后端不在同一域名，需要配置 CORS
2. **错误处理**: 始终检查返回的状态码，不要假设执行一定成功
3. **超时设置**: 对于长时间运行的代码，使用异步轮询方式
4. **安全性**: 对用户提交的代码进行必要的验证和限制
5. **性能**: 批量提交时使用 batch-submit 接口

## 完整文档

详细 API 文档请参考：`JUDGE0_API_DOC.md`
