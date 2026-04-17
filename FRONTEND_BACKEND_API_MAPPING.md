# aicoding-frontend 与 AiCooding 接口对照表

## 范围
- 前端仓库: `C:\Users\laoma\Projects\aicoding-frontend`
- 后端仓库: `C:\Users\laoma\PycharmProjects\AiCooding`
- 对照依据:
  - 前端接口调用（`request.get/post/put/patch/delete`）
  - 后端路由定义（`AiCooding/urls.py` + `api/urls.py`）

## 关键前提
- 后端统一前缀是 `/api/`（由 `AiCooding/urls.py` 挂载）
- 前端 `axios` 配置 `baseURL: '/api'`
- 前端大量代码又写了 `'/api/xxx'`，开发环境依赖 Vite 代理 `rewrite(/^\/api/, '')` 才能转发成功

---

## 已匹配接口

| 前端调用 | 前端位置（示例） | 后端路由 | 结果 |
|---|---|---|---|
| `POST /api/auth/jwt/login/` | `src/components/Login.vue:83` | `POST /api/auth/jwt/login/` | 匹配 |
| `POST /api/auth/jwt/logout/` | `src/components/MainPage.vue:324` | `POST /api/auth/jwt/logout/` | 匹配 |
| `GET /api/auth/jwt/me/` | `src/components/MainPage.vue:171`（共 7 处） | `GET /api/auth/jwt/me/` | 匹配 |
| `POST /auth/send-verification-code/` | `src/components/Register.vue:99` | `POST /api/auth/send-verification-code/` | 匹配（依赖 `baseURL`） |
| `POST /auth/verify-code/` | `src/components/Register.vue:121` | `POST /api/auth/verify-code/` | 匹配（依赖 `baseURL`） |
| `POST /auth/register-with-code/` | `src/components/Register.vue:127` | `POST /api/auth/register-with-code/` | 匹配（依赖 `baseURL`） |
| `GET /api/admin/users/` | `src/components/AdminPage.vue:248`、`src/components/UserManagement.vue:151` | `GET /api/admin/users/` | 匹配 |
| `GET /api/admin/statistics/users/` | `src/components/AdminPage.vue:432` | `GET /api/admin/statistics/users/` | 匹配 |
| `GET /api/leetcode/problems/` | `src/components/MainPage.vue:198`（共 6 处） | `GET /api/leetcode/problems/` | 匹配 |
| `GET /api/leetcode/problems/${id}/` | `src/components/AIJudge.vue:177` | `GET /api/leetcode/problems/<int:problem_id>/` | 匹配 |
| `GET /api/leetcode/problems/${this.problemId}/` | `src/components/ProblemDetail.vue:380` | `GET /api/leetcode/problems/<int:problem_id>/` | 匹配 |
| `GET /api/leetcode/stats/` | `src/components/AdminPage.vue:399` | `GET /api/leetcode/stats/` | 匹配 |
| `GET /api/user/completions/` | `src/components/MainPage.vue:351`（共 3 处） | `GET /api/user/completions/` | 匹配 |
| `POST /api/ai/chat/` | `src/components/AIChat.vue:223`（共 3 处） | `POST /api/ai/chat/` | 匹配 |
| `POST /api/ai/code-help/` | `src/components/AIChat.vue:283`（共 3 处） | `POST /api/ai/code-help/` | 匹配 |
| `POST /api/ai/judge/submit-and-complete/` | `src/components/AIJudge.vue:217`、`src/components/ProblemDetail.vue:612` | `POST /api/ai/judge/submit-and-complete/` | 匹配 |
| `GET /api/judge0/languages/` | `src/components/CodeEditor.vue:111` | `GET /api/judge0/languages/` | 匹配 |
| `POST /api/judge0/submit/` | `src/components/CodeEditor.vue:199` | `POST /api/judge0/submit/` | 匹配 |

## 不匹配接口（需改造）

| 前端调用 | 前端位置（示例） | 后端现状 | 建议 |
|---|---|---|---|
| `PATCH /api/admin/users/${user.id}/` | `src/components/UserManagement.vue:218`、`:250` | `/api/admin/users/<int:pk>/` 仅支持 `GET`；`PATCH` 在 `/api/admin/users/<int:pk>/role/` | 前端改调用 `/api/admin/users/${id}/role/`，或后端给 `/admin/users/<pk>/` 增加 `PATCH` |
| `POST /api/leetcode/problems/` | `src/components/ProblemManagement.vue:498` | `/api/leetcode/problems/` 仅 `GET` | 若需要后台题库管理，后端补 `POST` |
| `PUT /api/leetcode/problems/${problem_id}/` | `src/components/ProblemManagement.vue:488` | `/api/leetcode/problems/<int:problem_id>/` 仅 `GET` | 后端补 `PUT/PATCH` 或前端改走已有管理接口 |
| `DELETE /api/leetcode/problems/${id}/` | `src/components/ProblemManagement.vue:457`、`:424` | `/api/leetcode/problems/<int:problem_id>/` 仅 `GET` | 后端补 `DELETE`（含权限控制） |

---

## 路由依据
- `AiCooding/urls.py`：`path('api/', include('api.urls'))`
- `api/urls.py`：认证、用户管理、题库、Judge0、Qwen、AI 判题等接口定义

## 建议优先级
1. 先解决 `UserManagement` 的 `PATCH` 路由不一致（影响管理员核心操作）
2. 再确认 `ProblemManagement` 是“前端预留”还是“确需后端 CRUD”
3. 统一前端请求风格（建议全用不带 `/api` 的相对路径，避免 `baseURL + /api` 双前缀耦合）
