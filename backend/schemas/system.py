from pydantic import BaseModel, Field, field_validator


class NamePayloadSchema(BaseModel):
    name: str = Field(min_length=1, max_length=100)

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str):
        text = value.strip()
        if not text:
            raise ValueError("名称不能为空")
        return text

