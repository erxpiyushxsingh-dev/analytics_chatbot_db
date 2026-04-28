"""
FastAPI routes for the analytics chatbot.
"""

import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException

from api.models import (
    ChartType,
    HealthResponse,
    QueryRequest,
    QueryResponse,
    QueryStatus,
    SchemaResponse,
)
from services.db_service import db_service
from services.llm_service import llm_service
from services.sql_validator import sql_validator
from services.chart_service import chart_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Check service health."""
    db_ok = await db_service.test_connection()
    llm_ok = llm_service.is_available
    return HealthResponse(
        status="ok" if db_ok else "degraded",
        database="connected" if db_ok else "disconnected",
        llm="available" if llm_ok else "no_api_key",
    )


@router.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    Main endpoint: natural language → SQL → result → chart data.

    Pipeline:
        1. LLM generates SQL from the user question
        2. SQL validator checks for safety
        3. Database executes the validated query
        4. Results are converted to chart-friendly format
        5. Optional LLM explanation of results
    """
    # Step 1: Generate SQL
    try:
        sql = await llm_service.generate_sql(request.question)
    except Exception as e:
        logger.error(f"LLM generation error: {e}")
        return QueryResponse(
            status=QueryStatus.llm_failed,
            question=request.question,
            error=f"LLM generation failed: {e}",
        )

    # Step 2: Validate SQL
    is_valid, errors = sql_validator.validate(sql)
    if not is_valid:
        return QueryResponse(
            status=QueryStatus.validation_failed,
            question=request.question,
            sql=sql,
            validation_errors=errors,
            error="SQL validation failed: " + "; ".join(errors),
        )

    # Sanitize (defense in depth)
    sql = sql_validator.sanitize(sql)

    # Step 3: Execute query
    try:
        columns, rows, row_count = await db_service.execute_query(sql)
    except Exception as e:
        logger.error(f"Query execution error: {e}")
        return QueryResponse(
            status=QueryStatus.execution_failed,
            question=request.question,
            sql=sql,
            error=f"Query execution failed: {e}",
        )

    # Step 4: Chart data conversion
    chart_data = None
    if rows:
        chart_type_str = (
            request.chart_type.value
            if request.chart_type != ChartType.auto
            else "auto"
        )
        chart_result = chart_service.convert(columns, rows, chart_type_str)
        if chart_result:
            chart_data = chart_result

    # Step 5: Optional explanation
    explanation = None
    if request.include_explanation and rows:
        try:
            explanation = await llm_service.explain_result(
                request.question, sql, columns, rows
            )
        except Exception as e:
            logger.warning(f"Explanation generation failed: {e}")

    return QueryResponse(
        status=QueryStatus.success,
        question=request.question,
        sql=sql,
        columns=columns,
        rows=rows,
        row_count=row_count,
        explanation=explanation,
        chart=chart_data,
    )


@router.get("/schema", response_model=SchemaResponse)
async def get_schema():
    """Return the current database schema information."""
    try:
        schema_info = await db_service.get_schema_info()
        return SchemaResponse(tables=schema_info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch schema: {e}")


@router.post("/setup")
async def setup_database():
    """Initialize the database with schema and seed data."""
    base = Path(__file__).resolve().parent.parent
    schema_path = base / "schema.sql"
    seed_path = base / "seed_data.sql"

    try:
        if schema_path.exists():
            script = schema_path.read_text()
            await db_service.execute_script(script)
        else:
            raise HTTPException(status_code=404, detail="schema.sql not found")

        if seed_path.exists():
            script = seed_path.read_text()
            await db_service.execute_script(script)
        else:
            raise HTTPException(status_code=404, detail="seed_data.sql not found")

        return {"status": "ok", "message": "Database initialized with schema and seed data"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Setup failed: {e}")
