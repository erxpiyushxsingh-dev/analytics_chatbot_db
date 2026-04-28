"""
SQL Safety Validator Service.
Critical security layer that validates SQL before execution.
Prevents SQL injection and enforces read-only access.
"""

import re
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)

# Tables allowed in queries (must match the schema)
ALLOWED_TABLES = {"users", "products", "orders", "order_items", "branches"}

# Forbidden DDL/DML keywords
FORBIDDEN_KEYWORDS = {
    "DROP", "DELETE", "INSERT", "UPDATE", "TRUNCATE",
    "ALTER", "CREATE", "GRANT", "REVOKE", "COMMIT",
    "ROLLBACK", "EXECUTE", "EXEC", "MERGE",
}

# Regex patterns that indicate SQL injection attempts
INJECTION_PATTERNS = [
    (r";\s*\w+", "Multiple statements detected"),
    (r"--", "SQL comment detected"),
    (r"/\*", "Block comment detected"),
    (r"\bor\b\s+1\s*=\s*1", "Tautology injection pattern"),
    (r"\bunion\s+select\b", "UNION SELECT injection"),
    (r"\bexec\b", "Command execution keyword"),
    (r"\bxp_\w+", "Extended procedure call"),
    (r"\bwaitfor\b", "Time-based injection pattern"),
    (r"\bsleep\b", "Sleep-based injection pattern"),
    (r"\bbenchmark\b", "Benchmark injection pattern"),
]


class SQLValidatorService:
    """Validates SQL queries for safety before execution."""

    def validate(self, sql: str) -> Tuple[bool, List[str]]:
        """
        Validate a SQL query for safety.

        Args:
            sql: SQL query string to validate

        Returns:
            Tuple of (is_valid, list_of_error_messages)
        """
        errors: List[str] = []

        if not sql or not sql.strip():
            return False, ["Query is empty"]

        sql_stripped = sql.strip()

        self._check_forbidden_keywords(sql_stripped, errors)
        self._check_injection_patterns(sql_stripped, errors)
        self._check_allowed_operation(sql_stripped, errors)
        self._check_table_names(sql_stripped, errors)
        self._check_limit(sql_stripped, errors)
        self._check_subqueries(sql_stripped, errors)

        is_valid = len(errors) == 0
        if is_valid:
            logger.info("SQL validation passed")
        else:
            logger.warning(f"SQL validation failed: {errors}")
        return is_valid, errors

    def sanitize(self, sql: str) -> str:
        """
        Strip trailing semicolons and comments from a query.
        Validation should catch these; this is a defense-in-depth measure.
        """
        sql = sql.rstrip(";").strip()
        sql = re.sub(r"--.*$", "", sql, flags=re.MULTILINE)
        sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)
        return sql.strip()

    # --- Private checks ---

    @staticmethod
    def _check_forbidden_keywords(sql: str, errors: List[str]) -> None:
        upper = sql.upper()
        for kw in FORBIDDEN_KEYWORDS:
            if re.search(rf"\b{kw}\b", upper):
                errors.append(f"Forbidden keyword: {kw}. Only SELECT queries are allowed.")

    @staticmethod
    def _check_injection_patterns(sql: str, errors: List[str]) -> None:
        for pattern, description in INJECTION_PATTERNS:
            if re.search(pattern, sql, re.IGNORECASE):
                errors.append(f"Suspicious pattern: {description}")

    @staticmethod
    def _check_allowed_operation(sql: str, errors: List[str]) -> None:
        upper = sql.upper().lstrip()
        if not upper.startswith("SELECT") and not upper.startswith("WITH"):
            errors.append("Query must start with SELECT (CTE WITH…SELECT is also allowed).")

    @staticmethod
    def _check_table_names(sql: str, errors: List[str]) -> None:
        from_pattern = r"\bFROM\s+(\w+)"
        join_pattern = r"\bJOIN\s+(\w+)"
        for match in re.finditer(from_pattern, sql, re.IGNORECASE):
            table = match.group(1).lower()
            if table not in ALLOWED_TABLES:
                errors.append(f"Invalid table: '{table}'. Allowed: {sorted(ALLOWED_TABLES)}")
        for match in re.finditer(join_pattern, sql, re.IGNORECASE):
            table = match.group(1).lower()
            if table not in ALLOWED_TABLES:
                errors.append(f"Invalid table in JOIN: '{table}'. Allowed: {sorted(ALLOWED_TABLES)}")

    @staticmethod
    def _check_limit(sql: str, errors: List[str]) -> None:
        if "LIMIT" not in sql.upper():
            errors.append("Missing LIMIT clause. All queries must include LIMIT for safety.")
        else:
            match = re.search(r"LIMIT\s+(\d+)", sql, re.IGNORECASE)
            if match:
                limit_val = int(match.group(1))
                if limit_val > 1000:
                    errors.append(f"LIMIT {limit_val} exceeds maximum of 1000.")

    @staticmethod
    def _check_subqueries(sql: str, errors: List[str]) -> None:
        # Block nested subqueries beyond one level to limit complexity
        depth = sql.count("(SELECT") + sql.count("( select")
        if depth > 2:
            errors.append("Subquery nesting too deep (max 2 levels).")


# Singleton instance
sql_validator = SQLValidatorService()
