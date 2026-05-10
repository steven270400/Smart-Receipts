# SmartReceipts

SmartReceipts 是一个智能票据管理系统，包含 FastAPI 后端和 Vue 3 前端。系统覆盖票据图片上传、OCR 识别、规则提取、可选 LLM 候选选择、账单入库、账单管理、分类/支付方式维护和统计分析。

## 功能特性

- 票据 OCR：上传票据图片或文件，提取文本并生成结构化账单候选。
- 规则提取：默认使用规则链路识别金额、交易时间、商家、分类和支付方式。
- 可选 LLM 增强：通过 Ollama 对规则候选进行字段选择和纠偏；不可用时自动回退规则结果。
- 账单管理：支持新增、查询、编辑和软删除。
- 维度管理：支持分类和支付方式的新增、重命名、删除；删除时迁移历史账单到默认“其他”。
- 统计分析：提供总览指标、分类占比、月度趋势、消费统计和分类分析页面。
- 统一响应：后端接口统一返回 `{ code, message, data }`。

## 技术栈

### 后端

- Python 3.10+
- FastAPI
- PyMySQL
- PaddleOCR
- Pydantic
- unittest
- 可选：Ollama

### 前端

- Vue 3
- Vite
- Vue Router
- Element Plus
- ECharts

### 数据库

- MySQL 8.0+ 或兼容版本

## 目录结构

```text
SmartReceipts/
├─ backend/
│  ├─ core/              # 统一响应、业务异常和异常处理器
│  ├─ prompts/           # LLM prompt 配置
│  ├─ routers/           # FastAPI 路由
│  ├─ schemas/           # Pydantic 请求模型
│  ├─ services/          # 业务服务
│  ├─ tests/             # 后端测试
│  ├─ db_service.py      # 数据库访问和初始化
│  └─ main.py            # 应用入口
├─ frontend/
│  ├─ src/api/           # 前端 API 封装
│  ├─ src/components/    # 通用组件
│  ├─ src/layout/        # 应用布局和导航
│  ├─ src/stores/        # 轻量状态模块
│  └─ src/views/         # 页面视图
├─ docs/                 # 系统、API 和数据库设计文档
├─ uploads/              # 本地上传文件，忽略提交
├─ AGENTS.md             # 仓库内编码代理工作约定
└─ README.md
```

## 环境变量

### 后端

后端读取 `backend/.env` 或进程环境变量：

```env
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=1234
DB_NAME=smartreceipts
```

可选配置：

```env
SKIP_DB_INIT=true
EXTRACT_LLM_ENABLE=true
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b
OLLAMA_TIMEOUT_S=6
```

说明：

- 未设置 `SKIP_DB_INIT=true` 时，后端启动会自动初始化数据库、表、索引、默认分类和默认支付方式。
- 默认分类：`餐饮`、`交通`、`生活缴费`、`购物`、`其他`。
- 默认支付方式：`支付宝`、`微信`、`余额`、`银行卡`、`现金`、`其他`。
- LLM 增强默认关闭；关闭或不可用时仍使用规则提取链路。

### 前端

前端读取 `frontend/.env`：

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## 快速开始

### 1. 启动后端

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
cd ..
uvicorn backend.main:app --reload
```

后端默认地址：`http://127.0.0.1:8000`

健康检查：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/test
```

### 2. 启动前端

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

Vite 会输出本地访问地址，通常是 `http://127.0.0.1:5173`。

## API 概览

所有接口成功响应格式：

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

错误响应保持相同结构，`code` 为非 0 业务错误码。

| Method | Path | 说明 |
|---|---|---|
| GET | `/test` | 健康检查 |
| GET | `/receipts` | 分页查询账单 |
| POST | `/receipts` | 新增账单 |
| PUT | `/receipts/{receipt_id}` | 更新账单 |
| DELETE | `/receipts/{receipt_id}` | 软删除账单 |
| GET | `/statistics` | 获取统计分析数据 |
| POST | `/ocr` | 上传票据并执行 OCR 与提取 |
| GET | `/system/categories` | 查询分类 |
| POST | `/system/categories` | 新增分类 |
| PUT | `/system/categories/{category_id}` | 重命名分类 |
| DELETE | `/system/categories/{category_id}` | 删除分类并迁移账单 |
| GET | `/system/payment-methods` | 查询支付方式 |
| POST | `/system/payment-methods` | 新增支付方式 |
| PUT | `/system/payment-methods/{payment_method_id}` | 重命名支付方式 |
| DELETE | `/system/payment-methods/{payment_method_id}` | 删除支付方式并迁移账单 |

更多接口细节见 [API 设计文档](docs/api_design.md)。

## 测试与构建

后端测试：

```powershell
python -m unittest discover backend\tests
```

前端构建：

```powershell
cd frontend
npm run build
```

## 关键约定

- 账单时间字段统一使用 `transaction_time`，格式为 `YYYY-MM-DD HH:MM:SS`。
- 账单删除采用软删除，业务查询默认过滤 `is_deleted = 0`。
- SQL 使用参数化查询，不拼接用户输入。
- 上传文件必须保存到 `uploads/`，该目录不提交到 Git。
- OCR 自动入库至少需要有效 `amount` 和 `transaction_time`。
- LLM 是可选增强，不应成为 OCR 主流程硬依赖。
- 不提交 `.venv/`、`venv/`、`node_modules/`、`frontend/dist/`、`uploads/`、`receipt.db`、IDE 文件或本地日志。

## 文档

- [系统设计](docs/system_design.md)
- [API 设计](docs/api_design.md)
- [数据库设计](docs/database_design.md)
- [前端说明](frontend/README.md)
