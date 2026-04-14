# SmartReceipts

中文 | [English](#english)

---

<a id="中文"></a>
## 中文

### 项目简介
SmartReceipts 是一个面向个人与小团队的智能票据管理系统，提供从票据图片上传、OCR 识别、结构化提取、账单入库到统计分析看板的完整流程。

核心思路是将“规则提取的稳定性”与“LLM 候选选择的灵活性”结合，在保证可用性的基础上提升识别质量。

### 核心能力
- OCR 上传识别：上传票据文件后提取文本行。
- 规则基线提取：从 OCR 文本中抽取金额、日期、商家、支付方式、分类。
- 可选 LLM 增强：在规则生成的候选集合上做字段选择与纠偏。
- 账单管理：支持新增、查询、编辑、软删除（soft delete）。
- 统计分析：提供总额、分类占比、月度趋势、最大支出等看板数据。
- 统一响应：所有接口返回 `{ code, message, data }`。

### 架构与数据流
#### 后端分层
- `backend/routers`：接口路由与请求编排
- `backend/services`：业务服务（receipt/stats/ocr）
- `backend/db_service.py`：数据库访问与 SQL
- `backend/schemas`：请求模型与校验
- `backend/core`：异常体系、错误处理、统一响应
- `backend/utils`：通用时间处理工具

#### 前端结构
- `frontend/src/views`：页面级视图（Dashboard / ReceiptManage / OcrConsole）
- `frontend/src/components`：可复用组件
- `frontend/src/api`：接口封装与统一响应处理

#### OCR + LLM 主链路
1. 前端上传文件到 `POST /ocr`。
2. 后端将文件保存到 `uploads/`（安全文件名）。
3. OCR 引擎输出文本行。
4. 提取服务先做规则基线提取，再按配置决定是否启用 LLM 候选选择。
5. 结果统一归一化到 `transaction_time` 字段并校验关键字段。
6. 可保存时写入 `receipts` 与 `receipt_sources`。
7. 接口返回统一结构，附带 OCR/LLM 元数据。

### API 概览
| Method | Path | 说明 |
|---|---|---|
| GET | `/receipts` | 分页查询账单（支持商家/分类/支付方式/时间区间过滤） |
| POST | `/receipts` | 新增账单 |
| PUT | `/receipts/{receipt_id}` | 更新账单 |
| DELETE | `/receipts/{receipt_id}` | 软删除账单 |
| GET | `/statistics` | 获取统计看板数据 |
| POST | `/ocr` | 上传票据并执行 OCR+提取流程 |

统一响应示例：

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

### 快速开始（完整可运行）
#### 1) 环境要求
- Python 3.10+（建议）
- Node.js 18+（建议）
- MySQL 8.0+（或兼容版本）
- 可选：Ollama（仅启用 LLM 增强时需要）

#### 2) 后端启动
```bash
cd backend
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# macOS/Linux
# source .venv/bin/activate
pip install -r requirements.txt
# Windows
copy .env.example .env
# macOS/Linux
# cp .env.example .env
cd ..
uvicorn backend.main:app --reload
```

后端默认地址：`http://127.0.0.1:8000`

说明：
- 默认会在启动时初始化数据库与基础维度数据（categories/payment_methods）。
- 若设置 `SKIP_DB_INIT=true`，将跳过自动初始化。

#### 3) 前端启动
```bash
cd frontend
npm install
# Windows
copy .env.example .env
# macOS/Linux
# cp .env.example .env
npm run dev
```

前端默认地址：Vite 输出地址（通常是 `http://127.0.0.1:5173`）。

确保 `frontend/.env` 中：

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

#### 4) 可选：启用 LLM 增强（Ollama）
在后端环境变量中设置（示例）：

```env
EXTRACT_LLM_ENABLE=true
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b
OLLAMA_TIMEOUT_S=6
```

不启用时系统仍会使用规则基线提取，功能可正常使用。

### 目录结构
```text
SmartReceipts/
├─ backend/
│  ├─ routers/
│  ├─ services/
│  ├─ schemas/
│  ├─ core/
│  ├─ db_service.py
│  └─ main.py
├─ frontend/
│  ├─ src/views/
│  ├─ src/components/
│  └─ src/api/
├─ docs/
│  ├─ system_design.md
│  ├─ api_design.md
│  └─ database_design.md
└─ uploads/
```

### 注意事项
- 时间字段统一使用 `transaction_time`（`YYYY-MM-DD HH:mm:ss`）。
- 业务查询默认基于 `is_deleted = 0`（软删除策略）。
- OCR 场景下仅在关键字段有效时自动入库；否则返回识别结果供人工确认。
- PaddleOCR 依赖较重，首次安装可能耗时较长。

---

<a id="english"></a>
## English

### Overview
SmartReceipts is an intelligent receipt management system for individuals and small teams. It covers the full flow from image upload, OCR, structured extraction, persistence, to analytics dashboards.

The core idea is to combine the stability of rule-based extraction with the flexibility of LLM candidate selection, improving extraction quality without sacrificing reliability.

### Key Features
- OCR upload pipeline: extract text lines from uploaded receipt files.
- Rule-based baseline extraction: infer amount, date, merchant, payment method, and category.
- Optional LLM enhancement: choose/refine fields from rule-generated candidate sets.
- Receipt CRUD: create, query, update, and soft delete.
- Analytics: total amount, category distribution, monthly trend, and top expense.
- Unified API contract: `{ code, message, data }` for all endpoints.

### Architecture & Data Flow
#### Backend Layers
- `backend/routers`: API routing and request orchestration
- `backend/services`: business services (receipt/stats/ocr)
- `backend/db_service.py`: database access and SQL
- `backend/schemas`: request models and validation
- `backend/core`: exception system, error handlers, unified responses
- `backend/utils`: shared time utilities

#### Frontend Structure
- `frontend/src/views`: page-level views (Dashboard / ReceiptManage / OcrConsole)
- `frontend/src/components`: reusable UI modules
- `frontend/src/api`: API wrappers with unified response handling

#### OCR + LLM Main Flow
1. Frontend uploads a file to `POST /ocr`.
2. Backend stores it in `uploads/` with a safe filename.
3. OCR engine returns text lines.
4. Extraction service runs baseline rules, then optionally applies LLM candidate selection.
5. Output is normalized to `transaction_time` and validated.
6. If valid, data is persisted into `receipts` and `receipt_sources`.
7. API returns the unified payload plus OCR/LLM metadata.

### API Overview
| Method | Path | Description |
|---|---|---|
| GET | `/receipts` | Paginated list with merchant/category/payment/time filters |
| POST | `/receipts` | Create a receipt |
| PUT | `/receipts/{receipt_id}` | Update a receipt |
| DELETE | `/receipts/{receipt_id}` | Soft delete a receipt |
| GET | `/statistics` | Get dashboard statistics |
| POST | `/ocr` | Upload receipt and run OCR + extraction |

Unified response example:

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

### Quick Start (Full Run Steps)
#### 1) Requirements
- Python 3.10+ (recommended)
- Node.js 18+ (recommended)
- MySQL 8.0+ (or compatible)
- Optional: Ollama (only for LLM enhancement)

#### 2) Start Backend
```bash
cd backend
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# macOS/Linux
# source .venv/bin/activate
pip install -r requirements.txt
# Windows
copy .env.example .env
# macOS/Linux
# cp .env.example .env
cd ..
uvicorn backend.main:app --reload
```

Backend default URL: `http://127.0.0.1:8000`

Notes:
- Database initialization and seed data run on startup by default.
- Set `SKIP_DB_INIT=true` to skip auto initialization.

#### 3) Start Frontend
```bash
cd frontend
npm install
# Windows
copy .env.example .env
# macOS/Linux
# cp .env.example .env
npm run dev
```

Frontend URL: Vite output URL (typically `http://127.0.0.1:5173`).

Ensure `frontend/.env` contains:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

#### 4) Optional: Enable LLM Enhancement (Ollama)
Set backend environment variables (example):

```env
EXTRACT_LLM_ENABLE=true
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b
OLLAMA_TIMEOUT_S=6
```

If disabled, the system still works with rule-based baseline extraction.

### Project Structure
```text
SmartReceipts/
├─ backend/
│  ├─ routers/
│  ├─ services/
│  ├─ schemas/
│  ├─ core/
│  ├─ db_service.py
│  └─ main.py
├─ frontend/
│  ├─ src/views/
│  ├─ src/components/
│  └─ src/api/
├─ docs/
│  ├─ system_design.md
│  ├─ api_design.md
│  └─ database_design.md
└─ uploads/
```

### Notes
- Use `transaction_time` as the unified time field (`YYYY-MM-DD HH:mm:ss`).
- Business queries are based on `is_deleted = 0` (soft delete strategy).
- In OCR flow, auto-persistence happens only when key fields are valid.
- PaddleOCR dependencies are relatively heavy; first-time installation may take longer.
