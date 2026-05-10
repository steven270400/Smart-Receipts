# System Design

SmartReceipts 采用前后端分离架构。后端提供统一 API、OCR/LLM 提取和数据库访问，前端提供管理端页面和统计图表。

## Backend Layering

- `backend/main.py`：FastAPI 应用入口，注册 CORS、异常处理器和路由。
- `backend/routers`：API 路由层，只负责参数接收、依赖解析和服务调用。
- `backend/services`：业务编排层，处理账单、统计、OCR、系统维度等用例。
- `backend/db_service.py`：数据库访问层，集中管理 SQL、连接、初始化和维度数据。
- `backend/schemas`：Pydantic 请求模型和参数校验。
- `backend/core`：统一响应、业务异常和异常处理器。
- `backend/prompts`：LLM prompt schema 与模板配置。

新增后端能力时，优先沿用 router -> service -> db_service 的分层。

## Frontend Structure

- `frontend/src/router`：路由配置和页面访问日志。
- `frontend/src/layout`：整体布局和侧边导航。
- `frontend/src/views`：页面视图，包括首页、OCR 控制台、账单管理、消费统计、分类分析、分类管理和支付方式管理。
- `frontend/src/components`：复用组件，包括图表、筛选器、表格和表单弹窗。
- `frontend/src/api`：API 封装，统一校验 `{ code, message, data }`。
- `frontend/src/stores`：轻量状态模块，例如操作日志。
- `frontend/src/utils`：通用工具，例如日期格式化。

## OCR And Extraction Flow

1. 前端将票据文件上传到 `POST /ocr`。
2. 后端通过安全文件名将上传文件保存到 `uploads/`。
3. OCR 引擎提取文本行。
4. 文本修复逻辑处理常见 OCR 粘连和误识别。
5. 规则提取生成金额、交易时间、商家、分类和支付方式候选。
6. 若 `EXTRACT_LLM_ENABLE=true`，LLM provider 使用 Ollama 对候选字段进行选择和纠偏。
7. LLM 不可用、超时或结果无效时，系统回退到规则提取结果。
8. 输出结果归一到 `transaction_time` 字段。
9. 当关键字段有效时自动入库，否则返回识别结果供人工确认。

## Data And Consistency Rules

- API 响应统一使用 `{ code, message, data }`。
- 账单时间字段统一使用 `transaction_time`，格式为 `YYYY-MM-DD HH:MM:SS`。
- 不重新引入旧的 `date` 字段作为持久化 API 合同。
- 账单删除采用软删除，业务查询默认过滤 `is_deleted = 0`。
- 分类和支付方式删除时，将已有账单迁移到默认 `其他`。
- SQL 必须使用参数化查询。
- 上传文件和本地运行数据不进入 Git 仓库。

## Logging And Observability

- 页面访问和用户操作在前端操作日志中记录。
- OCR 响应包含 OCR 耗时、LLM 启用状态和回退状态等元数据。
- 后端异常由统一异常处理器转换为统一响应结构。

## Development Flow

- 后端改动优先运行相关 `backend/tests/test_*`，公共接口变化运行 `python -m unittest discover backend\tests`。
- 前端改动至少运行 `npm run build`。
- 涉及页面、布局、图表或交互时，应在浏览器中打开对应页面验证。
- 数据库 schema、API 字段、OCR/LLM 输出结构发生变化时，同步更新测试和 `docs/`。
