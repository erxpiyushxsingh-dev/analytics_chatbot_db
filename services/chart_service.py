"""
Chart Data Conversion Service.
Converts SQL query results into chart-friendly JSON format
compatible with Chart.js, D3.js, and similar libraries.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from api.models import ChartData

logger = logging.getLogger(__name__)

# Color palette for charts (10 distinct colors)
PALETTE = [
    "#4E79A7", "#F28E2B", "#E15759", "#76B7B2", "#59A14F",
    "#EDC948", "#B07AA1", "#FF9DA7", "#9C755F", "#BAB0AC",
]


class ChartService:
    """Converts tabular query results into chart-friendly data structures."""

    def convert(
        self,
        columns: List[str],
        rows: List[Dict[str, Any]],
        chart_type: str = "auto",
    ) -> Optional[ChartData]:
        """
        Convert query results to a ChartData object.

        Args:
            columns: Column names from the query
            rows: Rows as list of dicts
            chart_type: 'bar', 'line', 'pie', 'scatter', or 'auto'

        Returns:
            ChartData or None if conversion is not possible
        """
        if not rows or not columns:
            return None

        if chart_type == "auto":
            chart_type = self._detect_chart_type(columns, rows)

        if chart_type == "bar":
            return self._bar(columns, rows)
        if chart_type == "line":
            return self._line(columns, rows)
        if chart_type == "pie":
            return self._pie(columns, rows)
        if chart_type == "scatter":
            return self._scatter(columns, rows)

        return self._bar(columns, rows)

    # --- Auto-detection ---

    @staticmethod
    def _detect_chart_type(columns: List[str], rows: List[Dict[str, Any]]) -> str:
        """Auto-detect best chart type from data shape."""
        if len(columns) < 2:
            return "bar"

        col_types = {col: ChartService._infer_type(rows, col) for col in columns}
        string_cols = [c for c, t in col_types.items() if t == "string"]
        numeric_cols = [c for c, t in col_types.items() if t == "numeric"]
        date_cols = [c for c in columns if "date" in c.lower() or "time" in c.lower()]

        if date_cols and numeric_cols:
            return "line"
        if string_cols and numeric_cols:
            return "pie" if len(rows) <= 8 else "bar"
        if len(numeric_cols) >= 2:
            return "scatter"
        return "bar"

    @staticmethod
    def _infer_type(rows: List[Dict[str, Any]], column: str) -> str:
        """Infer whether a column is numeric or string."""
        for row in rows:
            val = row.get(column)
            if val is None:
                continue
            if isinstance(val, (int, float)):
                return "numeric"
            try:
                float(val)
                return "numeric"
            except (ValueError, TypeError):
                return "string"
        return "string"

    # --- Chart builders ---

    @staticmethod
    def _bar(columns: List[str], rows: List[Dict[str, Any]]) -> ChartData:
        """Build bar chart data."""
        label_col, value_cols = ChartService._split_label_values(columns, rows)
        labels = [str(row.get(label_col, "")) for row in rows]

        datasets = []
        for i, vcol in enumerate(value_cols):
            datasets.append({
                "label": vcol,
                "data": [float(row.get(vcol, 0)) for row in rows],
                "backgroundColor": PALETTE[i % len(PALETTE)],
                "borderColor": PALETTE[i % len(PALETTE)],
                "borderWidth": 1,
            })

        return ChartData(
            chart_type="bar",
            labels=labels,
            datasets=datasets,
            title=f"{value_cols[0]} by {label_col}" if value_cols else None,
        )

    @staticmethod
    def _line(columns: List[str], rows: List[Dict[str, Any]]) -> ChartData:
        """Build line chart data."""
        label_col, value_cols = ChartService._split_label_values(columns, rows)
        labels = [str(row.get(label_col, "")) for row in rows]

        datasets = []
        for i, vcol in enumerate(value_cols):
            datasets.append({
                "label": vcol,
                "data": [float(row.get(vcol, 0)) for row in rows],
                "borderColor": PALETTE[i % len(PALETTE)],
                "backgroundColor": PALETTE[i % len(PALETTE)] + "33",
                "fill": False,
                "tension": 0.3,
            })

        return ChartData(
            chart_type="line",
            labels=labels,
            datasets=datasets,
            title=f"{value_cols[0]} over {label_col}" if value_cols else None,
        )

    @staticmethod
    def _pie(columns: List[str], rows: List[Dict[str, Any]]) -> ChartData:
        """Build pie chart data."""
        label_col, value_cols = ChartService._split_label_values(columns, rows)
        labels = [str(row.get(label_col, "")) for row in rows]
        vcol = value_cols[0] if value_cols else columns[1] if len(columns) > 1 else columns[0]
        data = [float(row.get(vcol, 0)) for row in rows]

        return ChartData(
            chart_type="pie",
            labels=labels,
            datasets=[{
                "label": vcol,
                "data": data,
                "backgroundColor": PALETTE[:len(data)],
                "borderColor": "#ffffff",
                "borderWidth": 2,
            }],
            title=f"{vcol} distribution by {label_col}",
        )

    @staticmethod
    def _scatter(columns: List[str], rows: List[Dict[str, Any]]) -> ChartData:
        """Build scatter chart data."""
        numeric_cols = [
            c for c in columns if ChartService._infer_type(rows, c) == "numeric"
        ]
        if len(numeric_cols) < 2:
            # Fallback to bar if not enough numeric columns
            return ChartService._bar(columns, rows)

        x_col, y_col = numeric_cols[0], numeric_cols[1]
        points = [
            {"x": float(row.get(x_col, 0)), "y": float(row.get(y_col, 0))}
            for row in rows
        ]

        return ChartData(
            chart_type="scatter",
            labels=[],
            datasets=[{
                "label": f"{y_col} vs {x_col}",
                "data": points,
                "backgroundColor": PALETTE[0],
                "borderColor": PALETTE[0],
                "pointRadius": 5,
            }],
            title=f"{y_col} vs {x_col}",
        )

    # --- Helpers ---

    @staticmethod
    def _split_label_values(
        columns: List[str], rows: List[Dict[str, Any]]
    ) -> Tuple[str, List[str]]:
        """
        Identify the label (categorical) column and value (numeric) columns.
        Returns (label_col, [value_cols]).
        """
        string_cols = [c for c in columns if ChartService._infer_type(rows, c) == "string"]
        numeric_cols = [c for c in columns if ChartService._infer_type(rows, c) == "numeric"]

        if string_cols:
            label_col = string_cols[0]
        elif numeric_cols:
            label_col = numeric_cols[0]
            numeric_cols = numeric_cols[1:]
        else:
            label_col = columns[0]
            numeric_cols = columns[1:]

        if not numeric_cols and len(columns) > 1:
            numeric_cols = [columns[1]]

        return label_col, numeric_cols


# Singleton instance
chart_service = ChartService()
