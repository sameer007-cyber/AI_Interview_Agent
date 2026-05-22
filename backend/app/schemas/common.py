from typing import Any, Generic, Optional, TypeVar
from pydantic import BaseModel, Field

DataT = TypeVar("DataT")


class HealthResponse(BaseModel):
    status: str = Field(..., description="Service health status")
    version: str = Field(..., description="Current application version")
    environment: str = Field(..., description="Runtime environment")
    message: str = Field(..., description="Human-readable status message")


class APIResponse(BaseModel, Generic[DataT]):
    success: bool = Field(default=True)
    data: Optional[DataT] = Field(default=None)
    message: str = Field(default="")
    error: Optional[str] = Field(default=None)


class ErrorResponse(BaseModel):
    success: bool = Field(default=False)
    error: str = Field(..., description="Error type or code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Any] = Field(default=None)
