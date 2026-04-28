"""
Database Connector Component
Supports both PostgreSQL and SQLite for the analytics chatbot.
"""

import sqlite3
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class QueryResult:
    """Data class for query results."""
    columns: List[str]
    rows: List[tuple]
    row_count: int
    success: bool
    error: Optional[str] = None


class DatabaseConnector:
    """Database connector supporting both PostgreSQL and SQLite."""
    
    def __init__(self, db_type: str = 'sqlite', **kwargs):
        """
        Initialize database connector.
        
        Args:
            db_type: 'sqlite' or 'postgresql'
            **kwargs: Database connection parameters
                - For SQLite: db_path (path to .db file)
                - For PostgreSQL: host, port, database, user, password
        """
        self.db_type = db_type.lower()
        self.connection = None
        self.kwargs = kwargs
        
        if self.db_type not in ['sqlite', 'postgresql']:
            raise ValueError(f"Unsupported database type: {db_type}")
    
    def connect(self) -> bool:
        """
        Establish database connection.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            if self.db_type == 'sqlite':
                db_path = self.kwargs.get('db_path', 'analytics.db')
                self.connection = sqlite3.connect(db_path)
                self.connection.row_factory = sqlite3.Row  # Return rows as dictionaries
                logger.info(f"Connected to SQLite database: {db_path}")
                
            elif self.db_type == 'postgresql':
                try:
                    import psycopg2
                except ImportError:
                    raise ImportError(
                        "psycopg2 is required for PostgreSQL. "
                        "Install with: pip install psycopg2-binary"
                    )
                
                self.connection = psycopg2.connect(
                    host=self.kwargs.get('host', 'localhost'),
                    port=self.kwargs.get('port', 5432),
                    database=self.kwargs.get('database', 'analytics'),
                    user=self.kwargs.get('user', 'postgres'),
                    password=self.kwargs.get('password', '')
                )
                logger.info(f"Connected to PostgreSQL database: {self.kwargs.get('database')}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to database: {str(e)}")
            return False
    
    def disconnect(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("Database connection closed")
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> QueryResult:
        """
        Execute a SELECT query and return results.
        
        Args:
            query: SQL SELECT query
            params: Optional query parameters
            
        Returns:
            QueryResult object with query results
        """
        if not self.connection:
            if not self.connect():
                return QueryResult(
                    columns=[],
                    rows=[],
                    row_count=0,
                    success=False,
                    error="Database connection failed"
                )
        
        try:
            cursor = self.connection.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # Fetch results
            rows = cursor.fetchall()
            
            # Get column names
            if self.db_type == 'sqlite':
                columns = [description[0] for description in cursor.description]
            else:  # PostgreSQL
                columns = [desc[0] for desc in cursor.description]
            
            # Convert rows to list of tuples
            if self.db_type == 'sqlite':
                rows = [tuple(row) for row in rows]
            
            row_count = len(rows)
            
            cursor.close()
            
            logger.info(f"Query executed successfully. Returned {row_count} rows.")
            
            return QueryResult(
                columns=columns,
                rows=rows,
                row_count=row_count,
                success=True
            )
            
        except Exception as e:
            error_msg = f"Query execution failed: {str(e)}"
            logger.error(error_msg)
            return QueryResult(
                columns=[],
                rows=[],
                row_count=0,
                success=False,
                error=error_msg
            )
    
    def execute_script(self, script_path: str) -> bool:
        """
        Execute a SQL script file (useful for schema setup).
        
        Args:
            script_path: Path to SQL script file
            
        Returns:
            True if successful, False otherwise
        """
        if not self.connection:
            if not self.connect():
                return False
        
        try:
            with open(script_path, 'r') as f:
                script = f.read()
            
            cursor = self.connection.cursor()
            
            if self.db_type == 'sqlite':
                # SQLite can execute entire script
                cursor.executescript(script)
            else:
                # PostgreSQL needs to execute statements separately
                # Split by semicolon and execute each statement
                statements = [stmt.strip() for stmt in script.split(';') if stmt.strip()]
                for statement in statements:
                    if statement:
                        cursor.execute(statement)
            
            self.connection.commit()
            cursor.close()
            
            logger.info(f"Script executed successfully: {script_path}")
            return True
            
        except Exception as e:
            logger.error(f"Script execution failed: {str(e)}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        Test database connection with a simple query.
        
        Returns:
            Tuple of (success, message)
        """
        try:
            result = self.execute_query("SELECT 1 as test")
            if result.success and result.row_count == 1:
                return True, "Database connection test successful"
            else:
                return False, result.error or "Connection test failed"
        except Exception as e:
            return False, f"Connection test failed: {str(e)}"
    
    def get_table_info(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Get information about a table's columns.
        
        Args:
            table_name: Name of the table
            
        Returns:
            List of column information dictionaries
        """
        if self.db_type == 'sqlite':
            query = f"PRAGMA table_info({table_name})"
        else:  # PostgreSQL
            query = f"""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = '{table_name}'
                ORDER BY ordinal_position
            """
        
        result = self.execute_query(query)
        if result.success:
            if self.db_type == 'sqlite':
                # Convert PRAGMA result to standard format
                columns = []
                for row in result.rows:
                    columns.append({
                        'column_name': row[1],
                        'data_type': row[2],
                        'is_nullable': 'YES' if row[3] == 0 else 'NO',
                        'column_default': row[4]
                    })
                return columns
            else:
                return [
                    {
                        'column_name': row[0],
                        'data_type': row[1],
                        'is_nullable': row[2],
                        'column_default': row[3]
                    }
                    for row in result.rows
                ]
        return []
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()


# Example usage
if __name__ == "__main__":
    # Test with SQLite
    print("Testing SQLite connector...")
    sqlite_db = DatabaseConnector('sqlite', db_path='analytics.db')
    
    # Test connection
    success, msg = sqlite_db.test_connection()
    print(f"Connection test: {success} - {msg}")
    
    # Execute a simple query
    result = sqlite_db.execute_query("SELECT name FROM sqlite_master WHERE type='table'")
    if result.success:
        print(f"Tables: {result.rows}")
    
    sqlite_db.disconnect()
    
    # Test with PostgreSQL (uncomment if PostgreSQL is available)
    # print("\nTesting PostgreSQL connector...")
    # pg_db = DatabaseConnector(
    #     'postgresql',
    #     host='localhost',
    #     port=5432,
    #     database='analytics',
    #     user='postgres',
    #     password='your_password'
    # )
    # 
    # success, msg = pg_db.test_connection()
    # print(f"Connection test: {success} - {msg}")
    # 
    # pg_db.disconnect()
