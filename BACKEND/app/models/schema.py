"""Pydantic models for request/response schemas."""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ──── Request Models ────

class ChatRequest(BaseModel):
    """Chat request model."""
    message: str = Field(..., min_length=1, max_length=5000)
    active_file: str = ""
    all_files: List[str] = []
    conversation_history: List[Dict[str, str]] = []
    conversation_id: str = ""
    session_id: str = ""
    active_quarter: str = "All"
    active_category: str = "All"
    stream: bool = False

    class Config:
        example = {
            "message": "What were the top 5 companies by revenue?",
            "active_file": "sales_data.csv",
            "all_files": ["sales_data.csv"],
            "stream": False,
        }


class FilterRequest(BaseModel):
    """Data filtering request."""
    filters: Dict[str, Any] = Field(default_factory=dict)
    sort_col: Optional[str] = None
    sort_asc: bool = True
    limit: int = Field(default=200, le=2000)


class AggregateRequest(BaseModel):
    """Data aggregation request."""
    group_col: str
    value_col: str
    agg_func: str = "sum"
    top_n: int = Field(default=15, le=50)


class TimeSeriesRequest(BaseModel):
    """Time series analysis request."""
    date_col: str
    value_col: str
    freq: str = "M"  # M=monthly, Q=quarterly, Y=yearly
    agg_func: str = "sum"


# ──── Response Models ────

class StreamChunk(BaseModel):
    """Streaming response chunk."""
    status: str  # classifying | loading | generating | token | chart | done | error
    token: Optional[str] = None
    chart: Optional[Dict[str, Any]] = None
    table: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    step: Optional[int] = None


class ChatResponse(BaseModel):
    """Chat response model."""
    intent: str
    answer: str
    chart_config: Optional[Dict[str, Any]] = None
    dashboard_config: Optional[Dict[str, Any]] = None
    table_data: List[Dict[str, Any]] = []
    table_columns: List[str] = []
    active_file: str = ""
    error: Optional[str] = None
    context_used: Optional[str] = None  # Retrieved context for transparency


class FileUploadResponse(BaseModel):
    """File upload response."""
    name: str
    rows: int
    columns: int
    numeric_cols: List[str]
    categorical_cols: List[str]
    datetime_cols: List[str]
    schema: List[Dict[str, Any]]


class UploadResponse(BaseModel):
    """Bulk upload response."""
    uploaded: List[FileUploadResponse]
    errors: List[str]


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    ollama_status: str
    vector_store_status: str
    message: Optional[str] = None


# ──── Data Models ────

@dataclass
class ColumnMeta:
    """Column metadata."""
    name: str
    dtype: str
    nulls: int
    unique_count: int
    min_val: Optional[float] = None
    max_val: Optional[float] = None
    mean_val: Optional[float] = None
    top_values: List[tuple] = field(default_factory=list)


@dataclass
class CSVFile:
    """Loaded CSV file representation."""
    name: str
    df: Any  # pandas DataFrame
    row_count: int
    columns: List[ColumnMeta]
    numeric_cols: List[str]
    categorical_cols: List[str]
    datetime_cols: List[str]
