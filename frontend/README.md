# SmartReceipts Frontend

SmartReceipts 前端是基于 Vue 3、Vite、Element Plus 和 ECharts 的管理端应用，负责票据上传、账单管理、统计分析、分类管理和支付方式管理。

## 页面模块

- `/homepage`：系统首页，展示总览指标、分类占比、月度趋势、最高支出和操作日志。
- `/ocr`：OCR 控制台，上传票据文件并查看识别、提取和入库结果。
- `/receipts`：账单管理，支持筛选、新增、编辑和删除账单。
- `/analytics/overview`：消费统计，展示整体消费分析。
- `/analytics/category`：分类分析，展示分类维度的统计结果。
- `/system/categories`：分类管理，维护账单分类。
- `/system/payment-methods`：支付方式管理，维护支付方式。

## 技术栈

- Vue 3
- Vite
- Vue Router
- Element Plus
- ECharts

## 环境变量

复制环境变量模板：

```powershell
Copy-Item .env.example .env
```

配置后端 API 地址：

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## 开发命令

安装依赖：

```powershell
npm install
```

启动开发服务器：

```powershell
npm run dev
```

生产构建：

```powershell
npm run build
```

本地预览构建产物：

```powershell
npm run preview
```

## 代码结构

```text
frontend/
├─ src/api/           # API 请求封装
├─ src/components/    # 复用组件
├─ src/composables/   # 组合式逻辑
├─ src/layout/        # 布局和导航
├─ src/router/        # 路由配置
├─ src/stores/        # 轻量状态模块
├─ src/utils/         # 通用工具
└─ src/views/         # 页面视图
```

## 前端约定

- API 封装统一校验后端 `{ code, message, data }` 响应，页面层只处理 `data`。
- 日期和表单时间值保持与后端 `transaction_time` 格式兼容。
- UI 沿用 Element Plus 和现有 CSS 变量，不引入新的 UI 框架。
- 图表优先使用 ECharts。
- 新增页面时同步更新路由、布局导航和 `activeMenu`。
