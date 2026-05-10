# Database Design

SmartReceipts 使用 MySQL 保存分类、支付方式、账单和 OCR 来源信息。`init_db()` 会创建数据库、表、索引，并初始化默认维度数据。

## Connection

数据库连接配置来自环境变量：

- `DB_HOST`，默认 `127.0.0.1`
- `DB_PORT`，默认 `3306`
- `DB_USER`，默认 `root`
- `DB_PASSWORD`，默认 `1234`
- `DB_NAME`，默认 `smartreceipts`

设置 `SKIP_DB_INIT=true` 可跳过启动时数据库初始化。

## Core Tables

### `categories`

- `id` BIGINT PK AUTO_INCREMENT
- `name` VARCHAR(100) UNIQUE NOT NULL

默认数据：

- `餐饮`
- `交通`
- `生活缴费`
- `购物`
- `其他`

### `payment_methods`

- `id` BIGINT PK AUTO_INCREMENT
- `name` VARCHAR(100) UNIQUE NOT NULL

默认数据：

- `支付宝`
- `微信`
- `余额`
- `银行卡`
- `现金`
- `其他`

### `receipts`

- `id` BIGINT PK AUTO_INCREMENT
- `merchant` VARCHAR(255) NOT NULL
- `amount` DECIMAL(12,2) NOT NULL
- `transaction_time` DATETIME NOT NULL
- `category_id` BIGINT NOT NULL FK -> `categories.id`
- `payment_method_id` BIGINT NOT NULL FK -> `payment_methods.id`
- `notes` TEXT NULL
- `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
- `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
- `is_deleted` TINYINT(1) NOT NULL DEFAULT 0

### `receipt_sources`

- `id` BIGINT PK AUTO_INCREMENT
- `receipt_id` BIGINT UNIQUE NOT NULL FK -> `receipts.id`
- `source_type` ENUM('manual','ocr') NOT NULL
- `file_name` VARCHAR(255) NULL
- `raw_text` LONGTEXT NULL
- `extracted_json` JSON NULL
- `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP

## Indexes

- `idx_receipts_tci(transaction_time, category_id, is_deleted)`
- `idx_receipts_merchant(merchant)`

## Data Consistency Rules

- 账单使用软删除：删除操作只更新 `is_deleted`。
- 业务查询和统计默认只读取 `is_deleted = 0` 的记录。
- 时间字段只使用 `transaction_time`，不再使用旧 `date` 字段。
- 统计聚合基于 `receipts.transaction_time`。
- 删除分类时，相关账单迁移到默认分类 `其他`。
- 删除支付方式时，相关账单迁移到默认支付方式 `其他`。
- 所有包含用户输入的查询必须使用参数化 SQL。

## OCR Source Data

OCR 自动入库时会写入 `receipt_sources`，用于保留来源文件名、原始 OCR 文本和结构化提取 JSON。手动新增账单可以使用 `source_type='manual'` 标识来源。
