# API Design

本文档描述 SmartReceipts 当前后端接口约定。所有接口由 FastAPI 提供，默认地址为 `http://127.0.0.1:8000`。

## Unified Response

所有业务接口统一返回：

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

错误响应保持相同结构，`code` 为非 0 业务错误码，`message` 为可读错误信息。

## Health API

### `GET /test`

返回服务状态。

`data` 示例：

```json
{
  "status": "ok"
}
```

## Receipt APIs

### `GET /receipts`

分页查询未软删除账单。

Query params:

- `page`：整数，最小值 `1`。
- `size`：整数，范围 `1..1000`。
- `merchant`：可选，商家关键字。
- `category_id`：可选，分类 ID。
- `payment_method_id`：可选，支付方式 ID。
- `start_time`：可选，`YYYY-MM-DD` 或 `YYYY-MM-DD HH:MM:SS`。
- `end_time`：可选，`YYYY-MM-DD` 或 `YYYY-MM-DD HH:MM:SS`。

`data`:

- `list`：账单数组。
- `pagination`：`{ page, size, total }`。

### `POST /receipts`

新增账单。

Body fields:

- `merchant`：必填。
- `amount`：必填，金额大于等于 `0`。
- `transaction_time`：必填，格式 `YYYY-MM-DD HH:MM:SS`。
- `category_id` 或 `category`：逻辑必填。
- `payment_method_id` 或 `payment_method`：逻辑必填。
- `notes`：可选。

### `PUT /receipts/{receipt_id}`

更新账单，字段校验与新增账单一致。

### `DELETE /receipts/{receipt_id}`

软删除账单。数据库记录保留，业务查询默认过滤 `is_deleted = 0`。

## Statistics API

### `GET /statistics`

返回首页和统计分析所需数据。统计基于 `receipts.transaction_time` 和未软删除记录。

典型数据包括：

- 总金额。
- 账单数量。
- 分类占比。
- 月度趋势。
- 最高支出列表。

## OCR API

### `POST /ocr`

上传票据文件并执行 OCR、规则提取、可选 LLM 候选选择和自动入库。

Request:

- Content-Type: `multipart/form-data`
- Field: `file`

`data` includes:

- `ocr_result`：OCR 文本结果。
- `extracted_info`：结构化提取结果，时间字段使用 `transaction_time`。
- `saved`：是否已自动入库。
- `save_reason`：入库或未入库原因。
- `ocr_meta`：OCR/LLM 元数据，例如耗时、LLM 是否启用、是否发生回退。

自动入库至少需要有效 `amount` 和 `transaction_time`。LLM 不可用时应回退到规则提取结果。

## System APIs

### `GET /system/categories`

查询分类列表。

### `POST /system/categories`

新增分类。

Body fields:

- `name`：分类名称，必填。

### `PUT /system/categories/{category_id}`

重命名分类。

Body fields:

- `name`：新的分类名称，必填。

### `DELETE /system/categories/{category_id}`

删除分类。已有账单迁移到默认分类 `其他`，避免破坏外键约束。

### `GET /system/payment-methods`

查询支付方式列表。

### `POST /system/payment-methods`

新增支付方式。

Body fields:

- `name`：支付方式名称，必填。

### `PUT /system/payment-methods/{payment_method_id}`

重命名支付方式。

Body fields:

- `name`：新的支付方式名称，必填。

### `DELETE /system/payment-methods/{payment_method_id}`

删除支付方式。已有账单迁移到默认支付方式 `其他`，避免破坏外键约束。
