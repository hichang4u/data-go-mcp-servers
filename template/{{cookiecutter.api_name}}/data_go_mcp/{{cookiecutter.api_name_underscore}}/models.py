"""Data models for {{ cookiecutter.api_display_name }} API."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ExampleItem(BaseModel):
    """응답 item 하나. alias 는 API 의 camelCase 필드명, 속성명은 snake_case."""

    model_config = ConfigDict(populate_by_name=True)

    item_id: Optional[str] = Field(default=None, alias="itemId", description="항목 ID")
    item_name: Optional[str] = Field(default=None, alias="itemNm", description="항목명")
