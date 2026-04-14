# Database Design

## Core Tables

### `categories`
- `id` BIGINT PK AUTO_INCREMENT
- `name` VARCHAR(100) UNIQUE NOT NULL

### `payment_methods`
- `id` BIGINT PK AUTO_INCREMENT
- `name` VARCHAR(100) UNIQUE NOT NULL

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
- Soft delete only: all business queries must include `is_deleted = 0`.
- Unified time field: `transaction_time` only; `date` is no longer used.
- Aggregation baseline: all statistics are generated from `receipts.transaction_time` and active records.
