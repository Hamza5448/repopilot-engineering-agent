"""Run API request and response contracts."""

from pydantic import BaseModel, Field


class CreateRunRequest(BaseModel):
    trigger_type: str = Field(min_length=1, max_length=64)
    base_sha: str = Field(min_length=7, max_length=64)
