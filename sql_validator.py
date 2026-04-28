"""
SQL Validator Component
Validates SQL queries before execution to prevent injection and ensure safety.
This is a CRITICAL component for security.
"""

import re
import sqlparse
from typing import Tuple, List, Optional


class SQLValidator:
    """Validates SQL queries for safety and correctness."""
    
    # Allowed operations - only SELECT for analytics
    ALLOWED_OPERATIONS = ['SELECT']
    
    # Forbidden keywords (DML/DQL that modify data)
    FORBIDDEN_KEYWORDS = [
        'DROP', 'DELETE', 'INSERT', 'UPDATE', 'TRUNCATE', 
        'ALTER', 'CREATE', 'GRANT', 'REVOKE', 'COMMIT', 'ROLLBACK'
    ]
    
    # Allowed tables from our schema
    ALLOWED_TABLES = ['users', 'products', 'orders', 'order_items']
    
    # Suspicious patterns (potential SQL injection)
    SUSPICIOUS_PATTERNS = [
        r';\s*\w+',  # Multiple statements
        r'--',       # SQL comments
        r'/\*',      # Multi-line comments
        r'\bor\s+1\s*=\s*1\b',  # SQL injection tautology
        r'\bunion\s+select\b',  # UNION injection
        r'\bexec\b',  # Command execution
        r'\bxp_\w+',  # SQL Server extended procedures
    ]
    
    def __init__(self):
        self.validation_errors = []
    
    def validate(self, query: str) -> Tuple[bool, List[str]]:
        """
        Validate a SQL query.
        
        Args:
            query: SQL query string to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        self.validation_errors = []
        
        # Basic checks
        if not query or not query.strip():
            self.validation_errors.append("Query is empty")
            return False, self.validation_errors
        
        query = query.strip()
        
        # Check for forbidden keywords
        self._check_forbidden_keywords(query)
        
        # Check for allowed operations
        self._check_allowed_operations(query)
        
        # Check for suspicious patterns
        self._check_suspicious_patterns(query)
        
        # Validate table names
        self._validate_table_names(query)
        
        # Validate LIMIT clause
        self._validate_limit_clause(query)
        
        # Parse and validate SQL syntax
        self._validate_sql_syntax(query)
        
        return len(self.validation_errors) == 0, self.validation_errors
    
    def _check_forbidden_keywords(self, query: str):
        """Check for forbidden SQL keywords."""
        query_upper = query.upper()
        for keyword in self.FORBIDDEN_KEYWORDS:
            # Use word boundaries to avoid false positives
            pattern = r'\b' + keyword + r'\b'
            if re.search(pattern, query_upper, re.IGNORECASE):
                self.validation_errors.append(
                    f"Forbidden keyword detected: {keyword}. "
                    "Only SELECT queries are allowed."
                )
    
    def _check_allowed_operations(self, query: str):
        """Ensure only allowed operations are present."""
        query_upper = query.upper()
        has_allowed = any(op in query_upper for op in self.ALLOWED_OPERATIONS)
        if not has_allowed:
            self.validation_errors.append(
                f"No allowed operation found. Must be one of: {self.ALLOWED_OPERATIONS}"
            )
    
    def _check_suspicious_patterns(self, query: str):
        """Check for potential SQL injection patterns."""
        for pattern in self.SUSPICIOUS_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                self.validation_errors.append(
                    f"Suspicious pattern detected: {pattern}. "
                    "Potential SQL injection attempt."
                )
    
    def _validate_table_names(self, query: str):
        """Validate that only allowed tables are referenced."""
        # Extract table names using regex
        # This is a simple approach - for production, use a proper SQL parser
        from_pattern = r'\bFROM\s+(\w+)'
        join_pattern = r'\bJOIN\s+(\w+)'
        
        tables_found = []
        
        for match in re.finditer(from_pattern, query, re.IGNORECASE):
            tables_found.append(match.group(1).lower())
        
        for match in re.finditer(join_pattern, query, re.IGNORECASE):
            tables_found.append(match.group(1).lower())
        
        for table in tables_found:
            if table not in self.ALLOWED_TABLES:
                self.validation_errors.append(
                    f"Invalid table name: '{table}'. "
                    f"Allowed tables: {self.ALLOWED_TABLES}"
                )
    
    def _validate_limit_clause(self, query: str):
        """Ensure LIMIT clause is present to prevent large result sets."""
        if 'LIMIT' not in query.upper():
            self.validation_errors.append(
                "Missing LIMIT clause. All queries must include LIMIT for safety."
            )
        else:
            # Validate LIMIT value is reasonable
            limit_match = re.search(r'LIMIT\s+(\d+)', query, re.IGNORECASE)
            if limit_match:
                limit_value = int(limit_match.group(1))
                if limit_value > 1000:
                    self.validation_errors.append(
                        f"LIMIT value too large: {limit_value}. Maximum allowed is 1000."
                    )
    
    def _validate_sql_syntax(self, query: str):
        """Validate SQL syntax using sqlparse."""
        try:
            parsed = sqlparse.parse(query)
            if not parsed:
                self.validation_errors.append("Failed to parse SQL query")
                return
            
            # Check if it's a valid statement
            for statement in parsed:
                if not statement.get_type():
                    self.validation_errors.append("Invalid SQL statement type")
        except Exception as e:
            self.validation_errors.append(f"SQL parsing error: {str(e)}")
    
    def sanitize_query(self, query: str) -> str:
        """
        Sanitize the query by removing potentially harmful elements.
        Note: This is a last resort - validation should prevent issues.
        
        Args:
            query: SQL query to sanitize
            
        Returns:
            Sanitized query
        """
        # Remove trailing semicolons to prevent multiple statements
        query = query.rstrip(';')
        
        # Remove comments
        query = re.sub(r'--.*$', '', query, flags=re.MULTILINE)
        query = re.sub(r'/\*.*?\*/', '', query, flags=re.DOTALL)
        
        return query.strip()


# Example usage and testing
if __name__ == "__main__":
    validator = SQLValidator()
    
    # Test cases
    test_queries = [
        "SELECT * FROM users LIMIT 10",  # Valid
        "SELECT name, email FROM users WHERE country = 'USA' LIMIT 100",  # Valid
        "DELETE FROM users",  # Invalid - forbidden keyword
        "SELECT * FROM users; DROP TABLE orders",  # Invalid - multiple statements
        "SELECT * FROM invalid_table LIMIT 10",  # Invalid - invalid table
        "SELECT * FROM users",  # Invalid - missing LIMIT
        "SELECT * FROM users WHERE 1=1 OR 'a'='a'",  # Invalid - suspicious pattern
    ]
    
    for query in test_queries:
        is_valid, errors = validator.validate(query)
        print(f"\nQuery: {query}")
        print(f"Valid: {is_valid}")
        if errors:
            print(f"Errors: {errors}")
