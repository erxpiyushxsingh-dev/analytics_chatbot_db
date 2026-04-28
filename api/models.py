"""
Pydantic models for API request/response schemas.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from enum import Enum


# --- Enums ---

class ChartType(str, Enum):
    bar = "bar"
    line = "line"
    pie = "pie"
    scatter = "scatter"
    auto = "auto"


class QueryStatus(str, Enum):
    success = "success"
    error = "error"
    validation_failed = "validation_failed"
    llm_failed = "llm_failed"
    execution_failed = "execution_failed"


# --- Request Models ---

class QueryRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Natural language question to convert to SQL",
        examples=["Show me total revenue by country"]
    )
    chart_type: ChartType = Field(
        default=ChartType.auto,
        description="Preferred chart type. Use 'auto' for automatic detection."
    )
    include_explanation: bool = Field(
        default=True,
        description="Whether to include a natural language explanation of results"
    )
    limit: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum number of rows to return"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "question": "What is the total revenue by country?",
                    "chart_type": "bar",
                    "include_explanation": True,
                    "limit": 100
                }
            ]
        }
    }


# --- Response Models ---

class ChartData(BaseModel):
    chart_type: str = Field(description="Type of chart (bar, line, pie, scatter)")
    labels: List[str] = Field(description="Labels for the chart axes/segments")
    datasets: List[Dict[str, Any]] = Field(
        description="Chart datasets with values and styling info"
    )
    title: Optional[str] = Field(default=None, description="Suggested chart title")


class QueryResponse(BaseModel):
    status: QueryStatus = Field(description="Status of the query processing")
    question: str = Field(description="Original natural language question")
    sql: Optional[str] = Field(default=None, description="Generated SQL query")
    columns: Optional[List[str]] = Field(default=None, description="Column names in result")
    rows: Optional[List[Dict[str, Any]]] = Field(default=None, description="Result rows as dicts")
    row_count: Optional[int] = Field(default=None, description="Number of rows returned")
    explanation: Optional[str] = Field(default=None, description="Natural language explanation")
    chart: Optional[ChartData] = Field(default=None, description="Chart-friendly data")
    error: Optional[str] = Field(default=None, description="Error message if any")
    validation_errors: Optional[List[str]] = Field(default=None, description="SQL validation errors")


class HealthResponse(BaseModel):
    status: str = Field(description="Health status")
    database: str = Field(description="Database connection status")
    llm: str = Field(description="LLM API status")


class SchemaResponse(BaseModel):
    tables: Dict[str, Dict[str, Any]] = Field(description="Schema information per table")
