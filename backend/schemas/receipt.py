from pydantic import BaseModel, Field, field_validator

from backend.utils.time_utils import parse_datetime


class ReceiptQuerySchema(BaseModel):
    page: int = Field(default=1, ge=1)
    size: int = Field(default=10, ge=1, le=1000)
    merchant: str | None = None
    keyword: str | None = None
    category_id: int | None = Field(default=None, ge=1)
    payment_method_id: int | None = Field(default=None, ge=1)
    start_time: str | None = None
    end_time: str | None = None

    @field_validator("merchant", "keyword")
    @classmethod
    def normalize_merchant(cls, value: str | None):
        if value is None:
            return None
        text = value.strip()
        return text or None

    @field_validator("start_time", "end_time")
    @classmethod
    def validate_time(cls, value: str | None):
        if not value:
            return None
        parse_datetime(value)
        return value


class ReceiptBaseSchema(BaseModel):
    merchant: str = Field(min_length=1, max_length=255)
    amount: float
    transaction_time: str
    category_id: int | None = Field(default=None, ge=1)
    payment_method_id: int | None = Field(default=None, ge=1)
    category: str | None = None
    payment_method: str | None = None
    notes: str | None = None

    @field_validator("merchant")
    @classmethod
    def clean_merchant(cls, value: str):
        text = value.strip()
        if not text:
            raise ValueError("????????")
        return text

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value: float):
        if value is None:
            raise ValueError("??????")
        if value < 0:
            raise ValueError("???????")
        return round(float(value), 2)

    @field_validator("transaction_time")
    @classmethod
    def validate_transaction_time(cls, value: str):
        parse_datetime(value)
        return value

    @field_validator("category", "payment_method")
    @classmethod
    def clean_optional_name(cls, value: str | None):
        if value is None:
            return None
        text = value.strip()
        return text or None


class ReceiptCreateSchema(ReceiptBaseSchema):
    pass


class ReceiptUpdateSchema(ReceiptBaseSchema):
    pass
