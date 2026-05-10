# AGENTS.md

本文件为在 SmartReceipts 仓库中工作的编码代理提供项目约定和操作指引。改代码前先阅读本文件、根目录 `README.md`，以及任务相关模块附近的实现。

## 项目概览

SmartReceipts 是一个智能票据管理系统，包含 FastAPI 后端和 Vue 3 前端。系统覆盖票据图片上传、OCR 识别、规则提取、可选 LLM 候选选择、账单入库、账单管理和统计分析。

- 后端：`backend/`，FastAPI + PyMySQL + PaddleOCR，负责 API、数据库访问、OCR/LLM 提取和业务服务。
- 前端：`frontend/`，Vue 3 + Vite + Element Plus + ECharts，负责管理端页面和图表展示。
- 文档：`docs/`，包含系统设计、API 设计和数据库设计。
- 上传目录：`uploads/`，保存 OCR 上传文件。不要提交本地上传文件或运行产物。

核心 API 响应统一为：

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

错误响应也应保持同样结构，只是 `code` 为业务错误码。

## 常用命令

后端依赖安装：

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd ..
```

后端启动：

```powershell
uvicorn backend.main:app --reload
```

跳过启动时数据库初始化：

```powershell
$env:SKIP_DB_INIT="true"
uvicorn backend.main:app --reload
```

后端测试：

```powershell
python -m unittest discover backend\tests
```

前端依赖安装与开发：

```powershell
cd frontend
npm install
npm run dev
```

前端构建：

```powershell
cd frontend
npm run build
```

默认服务地址：

- 后端：`http://127.0.0.1:8000`
- 前端：Vite 输出地址，通常为 `http://127.0.0.1:5173`

## 后端结构

- `backend/main.py`：FastAPI 应用入口，注册 CORS、异常处理和路由。
- `backend/routers/`：API 路由层，只做参数接收、依赖解析和服务调用。
- `backend/services/`：业务编排层，处理用例流程和异常转换。
- `backend/db_service.py`：数据库访问层，集中管理 SQL、连接、初始化和维度数据。
- `backend/schemas/`：Pydantic 请求模型和参数校验。
- `backend/core/`：统一响应、业务异常和异常处理器。
- `backend/utils/`：通用工具。
- `backend/tests/`：unittest 测试。

新增后端能力时，优先沿用当前分层：router 调 service，service 调 db_service 或 OCR/LLM 模块。

## 后端约定

- 所有成功接口返回 `success_response(...)`。
- 参数错误使用 `ParamException`，数据库错误使用 `DatabaseException`，OCR 错误使用 `OCRException`，LLM 错误使用 `LLMException`，不存在资源使用 `NotFoundException`。
- 不要在 router 中直接返回裸字典作为业务响应，除非它已经经过统一响应封装。
- 账单时间字段统一使用 `transaction_time`，格式为 `YYYY-MM-DD HH:MM:SS`。
- 不要重新引入旧的 `date` 字段作为持久化 API 合同。OCR 中间结果可以临时使用 `date`，但返回和入库前应归一到 `transaction_time`。
- 账单删除采用软删除，业务查询默认过滤 `is_deleted = 0`。
- SQL 必须使用参数化查询，不要拼接用户输入。
- 数据库 schema、API 字段、OCR/LLM 输出结构发生变化时，同步更新测试和 `docs/` 中对应文档。

## 数据库与环境变量

数据库连接配置来自环境变量：

- `DB_HOST`，默认 `127.0.0.1`
- `DB_PORT`，默认 `3306`
- `DB_USER`，默认 `root`
- `DB_PASSWORD`，默认 `1234`
- `DB_NAME`，默认 `smartreceipts`

`init_db()` 会创建数据库、表、索引，并初始化默认分类和支付方式。测试、接口 mock 或无需真实数据库时设置：

```powershell
$env:SKIP_DB_INIT="true"
```

默认维度：

- 分类：`餐饮`、`交通`、`生活缴费`、`购物`、`其他`
- 支付方式：`支付宝`、`微信`、`余额`、`银行卡`、`现金`、`其他`

删除分类或支付方式时，已有账单应迁移到默认 `其他`，不要破坏外键约束。

## OCR 与 LLM 约定

- OCR 上传入口为 `POST /ocr`，主流程在 `backend/services/ocr_service.py`。
- 上传文件必须通过 `build_safe_upload_path()` 生成安全文件名，保存到 `uploads/`。
- OCR 引擎封装在 `backend/ocr_service.py`。
- OCR 文本修复逻辑在 `backend/text_fixups.py` 和 OCR 服务调用链中。
- 规则提取在 `backend/extract_service.py`，这是默认可用链路。
- LLM 增强是可选能力，通过 `EXTRACT_LLM_ENABLE=true` 开启。
- LLM provider 当前为 Ollama，配置包括 `OLLAMA_HOST`、`OLLAMA_MODEL`、`OLLAMA_TIMEOUT_S`。
- LLM prompt 配置位于 `backend/prompts/receipt_selector_prompt.json`。修改 prompt schema 时同步更新 `backend/tests/test_llm_prompt_loader.py` 和 LLM 选择相关测试。
- OCR 自动入库只应在关键字段有效时发生，至少需要有效 `amount` 和 `transaction_time`。
- LLM 不可用时，系统应回退到规则提取结果，而不是让 OCR 主流程整体不可用。

## 前端结构

- `frontend/src/main.js`：Vue 应用入口，注册 router 和 Element Plus。
- `frontend/src/router/index.js`：路由配置和页面访问日志。
- `frontend/src/layout/`：整体布局和侧边导航。
- `frontend/src/views/`：页面级视图。
- `frontend/src/components/`：可复用组件。
- `frontend/src/components/dashboard/`：首页统计卡片和图表组件。
- `frontend/src/components/receipt/`：账单筛选、表格和表单弹窗。
- `frontend/src/api/`：接口封装和统一响应处理。
- `frontend/src/stores/`：轻量状态模块，例如操作日志。
- `frontend/src/utils/`：通用工具，例如日期格式化。

## 前端约定

- API 基础地址来自 `VITE_API_BASE_URL`，默认 `http://127.0.0.1:8000`。
- 前端 API 封装应校验 `{ code, message, data }`，视图层只接收 `data`。
- 新页面需要同时更新 router、布局导航和 `activeMenu`。
- UI 风格沿用 Element Plus、现有 CSS 变量和当前布局，不要引入新的 UI 框架。
- 图表优先使用 ECharts，避免手写复杂图表逻辑。
- 日期展示和表单时间值应保持与后端 `transaction_time` 格式兼容。
- 涉及页面、布局、图表或交互时，除了构建检查，还应在浏览器中打开对应页面人工验证。

## 测试与验证策略

后端改动：

- 规则提取、OCR 修复、LLM 选择：运行相关 `backend/tests/test_*`，至少覆盖被改模块。
- API 响应、异常处理或路由：运行 `python -m unittest discover backend\tests`。
- 数据库相关改动：确认 MySQL schema 初始化、软删除、维度迁移和参数化查询行为。

前端改动：

- 至少运行 `npm run build`。
- 涉及路由或页面导航时，手动检查对应路径。
- 涉及图表时，确认空数据、正常数据和较长文本不会破坏布局。

全栈改动：

- 后端启动后检查 `/test` 返回统一成功响应。
- 前端确认 `VITE_API_BASE_URL` 指向正在运行的后端。
- 验证相关接口仍返回统一响应结构。

## 工作流程

1. 先查看 `git status --short`，识别已有未提交改动。
2. 只修改任务相关文件，不回退用户已有改动。
3. 阅读相关 router、service、schema、db_service 和前端调用点后再下手。
4. 小步修改，保持行为与现有代码风格一致。
5. 改完运行最接近的测试或构建；如果无法运行，说明原因。
6. 汇报时列出改动文件、验证命令和残余风险。

## 不要做的事

- 不要提交 `.venv/`、`venv/`、`node_modules/`、`uploads/`、本地数据库或 IDE 产物。
- 不要把用户输入拼进 SQL。
- 不要绕过统一响应和统一异常处理。
- 不要在没有必要时修改数据库 schema 或 API 合同。
- 不要让 LLM 成为 OCR 流程的硬依赖。
- 不要引入新框架或大型依赖来解决局部问题。
- 不要重排大文件或进行无关格式化，避免扩大 diff。

## 当前环境提示

当前开发环境以 Windows PowerShell 为默认 shell，示例命令优先使用 PowerShell 语法。项目根目录为：

```text
C:\Users\User\PycharmProjects\SmartReceipts
```
