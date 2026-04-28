"""
LLM Service - OpenAI API compatible integration.
Generates SQL from natural language and explains query results.
"""

import logging
from typing import Optional

from openai import AsyncOpenAI

from config import config

logger = logging.getLogger(__name__)

# Schema definition embedded for prompt context
SCHEMA_CONTEXT = """
-- Branches table: stores D-Mart branch information
CREATE TABLE branches (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    area VARCHAR(100) NOT NULL
);

-- Users table: stores customer information with area and branch
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    country VARCHAR(100) NOT NULL,
    area VARCHAR(100) NOT NULL,
    branch_id INTEGER,
    CONSTRAINT fk_user_branch FOREIGN KEY (branch_id) REFERENCES branches(id)
);

-- Products table: stores product catalog
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    price DECIMAL(10, 2) NOT NULL CHECK (price > 0)
);

-- Orders table: stores order header information with branch
-- FK: user_id → users.id
-- FK: branch_id → branches.id
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    order_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total_amount DECIMAL(12, 2) NOT NULL CHECK (total_amount >= 0),
    branch_id INTEGER NOT NULL,
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_order_branch FOREIGN KEY (branch_id) REFERENCES branches(id)
);

-- Order Items table: stores individual items per order
-- FK: order_id → orders.id
-- FK: product_id → products.id
CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    price DECIMAL(10, 2) NOT NULL CHECK (price > 0),
    CONSTRAINT fk_order FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    CONSTRAINT fk_product FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT
);

Relationships:
- branches.id ← users.branch_id (one branch has many customers)
- branches.id ← orders.branch_id (one branch has many orders)
- users.id ← orders.user_id (one user has many orders)
- orders.id ← order_items.order_id (one order has many items)
- products.id ← order_items.product_id (one product appears in many order items)

Join patterns:
- orders JOIN branches ON orders.branch_id = branches.id (to get branch name)
- users JOIN branches ON users.branch_id = branches.id (to get branch name)
- users JOIN orders ON users.id = orders.user_id
- orders JOIN order_items ON orders.id = order_items.order_id
- order_items JOIN products ON order_items.product_id = products.id
- Full chain: branches → orders → order_items → products

Available dimensions for analysis:
- branches.name: Branch name (e.g., "D-Mart Andheri West", "D-Mart BKC", etc.)
- branches.area: Branch area (e.g., Andheri West, Bandra Kurla Complex, Powai, etc.)
- users.area: Customer area
- category: Product category (Groceries, Electronics, Home & Kitchen, Clothing, etc.)
- order_date: Date of order for time-based analysis

IMPORTANT: When querying by branch, always JOIN with branches table to get branch name, not branch_id.
"""

SQL_SYSTEM_PROMPT = """You are an expert SQL generator.
Convert the user's natural language question into a PostgreSQL SQL query.

Rules:
- ONLY generate SELECT queries
- NEVER use DELETE, UPDATE, INSERT, DROP, ALTER
- Always include LIMIT 100
- Use correct joins based on schema and foreign keys
- Use table and column names exactly as provided
- If ambiguous, make a reasonable assumption
- Use proper table aliases and JOIN syntax
- For aggregations, always include GROUP BY on non-aggregated columns
- Use meaningful column aliases (e.g., total_revenue, user_count)

Output: SQL query only. No explanation. No markdown. No backticks."""

EXPLANATION_SYSTEM_PROMPT = """You are a helpful data analyst assistant.
Given a user question, the SQL query that was run, and the query results,
provide a brief, clear explanation of what the data shows in 1-2 sentences.
Be concise and use plain language."""


class LLMService:
    """Async LLM service using OpenAI-compatible API."""

    def __init__(self):
        self._client: Optional[AsyncOpenAI] = None
        self._model = config.llm.model
        self._available = bool(config.llm.api_key)

    def _get_client(self) -> AsyncOpenAI:
        if not self._available:
            raise RuntimeError("LLM API key not configured. Set OPENAI_API_KEY.")
        if self._client is None:
            self._client = AsyncOpenAI(
                api_key=config.llm.api_key,
                base_url=config.llm.base_url,
            )
        return self._client

    @property
    def is_available(self) -> bool:
        return self._available

    async def generate_sql(self, question: str) -> str:
        """
        Generate a SQL query from a natural language question.

        Args:
            question: User's natural language question

        Returns:
            Generated SQL query string

        Raises:
            RuntimeError: If LLM is unavailable or generation fails
        """
        if not self._available:
            return self._fallback_sql(question)

        client = self._get_client()
        user_prompt = f"Schema:\n{SCHEMA_CONTEXT}\n\nUser Question: {question}"

        try:
            response = await client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": SQL_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=config.llm.temperature,
                max_tokens=config.llm.max_tokens,
            )
            sql = response.choices[0].message.content.strip()
            # Strip markdown code fences if present
            if sql.startswith("```"):
                sql = sql.split("\n", 1)[1] if "\n" in sql else sql[3:]
            if sql.endswith("```"):
                sql = sql[:-3]
            sql = sql.strip()
            logger.info(f"LLM generated SQL: {sql}")
            return sql

        except Exception as e:
            logger.error(f"LLM SQL generation failed: {e}")
            return self._fallback_sql(question)

    async def explain_result(
        self, question: str, sql: str, columns: list, rows: list
    ) -> Optional[str]:
        """
        Generate a natural language explanation of query results.

        Args:
            question: Original user question
            sql: SQL query that was executed
            columns: Column names
            rows: Result rows

        Returns:
            Explanation string or None
        """
        if not self._available:
            return self._fallback_explanation(question, rows)

        # Build a compact result summary for the LLM
        sample = rows[:5]
        result_text = (
            f"Columns: {columns}\n"
            f"Rows ({len(rows)} total): {sample}"
        )

        client = self._get_client()
        user_prompt = (
            f"User Question: {question}\n"
            f"SQL Query: {sql}\n"
            f"Result: {result_text}"
        )

        try:
            response = await client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": EXPLANATION_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.5,
                max_tokens=200,
            )
            explanation = response.choices[0].message.content.strip()
            logger.info("LLM generated explanation")
            return explanation

        except Exception as e:
            logger.error(f"LLM explanation failed: {e}")
            return self._fallback_explanation(question, rows)

    # --- Fallback methods (no API key) ---

    @staticmethod
    def _fallback_sql(question: str) -> str:
        """Pattern-matching fallback when no LLM API key is configured."""
        q = question.lower()

        # Revenue / sales queries
        if "revenue" in q and "area" in q:
            return "SELECT u.area, SUM(o.total_amount) AS total_revenue FROM users u JOIN orders o ON u.id = o.user_id GROUP BY u.area ORDER BY total_revenue DESC LIMIT 100"
        if "revenue" in q and "branch" in q:
            return "SELECT b.name AS branch_name, SUM(o.total_amount) AS total_revenue FROM orders o JOIN branches b ON o.branch_id = b.id GROUP BY b.name ORDER BY total_revenue DESC LIMIT 100"
        if "revenue" in q or "total sales" in q or "total amount" in q:
            return "SELECT SUM(o.total_amount) AS total_revenue FROM orders o LIMIT 100"
        if "revenue" in q and "month" in q or "revenue" in q and "date" in q:
            return "SELECT DATE(o.order_date) AS order_date, SUM(o.total_amount) AS daily_revenue FROM orders o GROUP BY DATE(o.order_date) ORDER BY order_date LIMIT 100"

        # Count by dimension queries
        if "count" in q and "user" in q and "area" in q:
            return "SELECT u.area, COUNT(*) AS user_count FROM users u GROUP BY u.area ORDER BY user_count DESC LIMIT 100"
        if "count" in q and "order" in q and "area" in q:
            return "SELECT u.area, COUNT(o.id) AS order_count FROM users u JOIN orders o ON u.id = o.user_id GROUP BY u.area ORDER BY order_count DESC LIMIT 100"
        if "count" in q and "order" in q and "branch" in q:
            return "SELECT b.name AS branch_name, COUNT(*) AS order_count FROM orders o JOIN branches b ON o.branch_id = b.id GROUP BY b.name ORDER BY order_count DESC LIMIT 100"
        if "count" in q and "product" in q and "category" in q:
            return "SELECT p.category, COUNT(*) AS product_count FROM products p GROUP BY p.category ORDER BY product_count DESC LIMIT 100"

        # Simple count queries
        if "count" in q and "user" in q:
            return "SELECT COUNT(*) AS user_count FROM users LIMIT 100"
        if "count" in q and "product" in q:
            return "SELECT COUNT(*) AS product_count FROM products LIMIT 100"
        if "count" in q and "order" in q:
            return "SELECT COUNT(*) AS order_count FROM orders LIMIT 100"

        # Group by area
        if "area" in q and ("revenue" in q or "sales" in q or "spending" in q):
            return "SELECT u.area, SUM(o.total_amount) AS total_revenue FROM users u JOIN orders o ON u.id = o.user_id GROUP BY u.area ORDER BY total_revenue DESC LIMIT 100"
        if "area" in q:
            return "SELECT u.area, COUNT(*) AS user_count FROM users u GROUP BY u.area ORDER BY user_count DESC LIMIT 100"

        # Group by branch
        if "branch" in q and ("revenue" in q or "sales" in q):
            return "SELECT b.name AS branch_name, SUM(o.total_amount) AS total_revenue FROM orders o JOIN branches b ON o.branch_id = b.id GROUP BY b.name ORDER BY total_revenue DESC LIMIT 100"
        if "branch" in q:
            return "SELECT b.name AS branch_name, COUNT(*) AS order_count FROM orders o JOIN branches b ON o.branch_id = b.id GROUP BY b.name ORDER BY order_count DESC LIMIT 100"

        # Group by category
        if "category" in q and ("revenue" in q or "sales" in q):
            return "SELECT p.category, SUM(oi.quantity * oi.price) AS category_revenue FROM products p JOIN order_items oi ON p.id = oi.product_id GROUP BY p.category ORDER BY category_revenue DESC LIMIT 100"
        if "category" in q:
            return "SELECT p.category, COUNT(*) AS product_count FROM products p GROUP BY p.category ORDER BY product_count DESC LIMIT 100"

        # Top products
        if "top" in q and "product" in q:
            return "SELECT p.name, SUM(oi.quantity) AS total_sold FROM products p JOIN order_items oi ON p.id = oi.product_id GROUP BY p.name ORDER BY total_sold DESC LIMIT 100"
        if "popular" in q or "best" in q and "product" in q:
            return "SELECT p.name, SUM(oi.quantity) AS total_sold FROM products p JOIN order_items oi ON p.id = oi.product_id GROUP BY p.name ORDER BY total_sold DESC LIMIT 100"

        # Average
        if "average" in q or "avg" in q:
            if "order" in q:
                return "SELECT AVG(total_amount) AS avg_order_value FROM orders LIMIT 100"
            if "price" in q or "product" in q:
                return "SELECT AVG(price) AS avg_price FROM products LIMIT 100"

        # Recent orders
        if "recent" in q or "latest" in q:
            return "SELECT o.id, u.name, o.order_date, o.total_amount FROM orders o JOIN users u ON o.user_id = u.id ORDER BY o.order_date DESC LIMIT 100"

        # User details
        if "user" in q and ("detail" in q or "info" in q or "show" in q):
            return "SELECT * FROM users LIMIT 100"

        # Product listing
        if "product" in q:
            return "SELECT * FROM products LIMIT 100"

        # Order listing
        if "order" in q:
            return "SELECT o.id, u.name, o.order_date, o.total_amount FROM orders o JOIN users u ON o.user_id = u.id ORDER BY o.order_date DESC LIMIT 100"

        return "SELECT * FROM users LIMIT 100"

    @staticmethod
    def _fallback_explanation(question: str, rows: list) -> Optional[str]:
        """Template-based fallback explanation with natural language."""
        if not rows:
            return "No results found for your query."
        
        q = question.lower()
        num_rows = len(rows)
        
        # Revenue/sales queries
        if "revenue" in q or "sales" in q or "total" in q:
            if "branch" in q:
                return f"Here's the revenue breakdown by branch across {num_rows} locations."
            if "area" in q:
                return f"Here's the revenue breakdown by area across {num_rows} regions."
            if "category" in q:
                return f"Here's the revenue breakdown by product category."
            val = rows[0] if rows else {}
            for k, v in val.items():
                if isinstance(v, (int, float)):
                    return f"The total revenue is ${v:,.2f}."
        
        # Count queries
        if "count" in q:
            if "branch" in q:
                return f"Here's the order count by branch across {num_rows} locations."
            if "area" in q:
                return f"Here's the customer count by area across {num_rows} regions."
            if "product" in q and "category" in q:
                return f"Here's the product count by category."
            val = rows[0] if rows else {}
            for k, v in val.items():
                if isinstance(v, (int, float)):
                    return f"The count is {int(v)}."
        
        # Top/best/popular queries
        if "top" in q or "best" in q or "popular" in q:
            if "product" in q:
                return f"Here are the top {num_rows} best-selling products."
            if "branch" in q:
                return f"Here are the top {num_rows} performing branches."
        
        # Average queries
        if "average" in q or "avg" in q:
            if "order" in q:
                return f"The average order value is shown below."
            if "price" in q or "product" in q:
                return f"The average product price is shown below."
            val = rows[0] if rows else {}
            for k, v in val.items():
                if isinstance(v, (int, float)):
                    return f"The average is {v:,.2f}."
        
        # Recent/latest queries
        if "recent" in q or "latest" in q:
            return f"Here are the {num_rows} most recent orders."
        
        # Generic breakdown
        if num_rows > 1:
            return f"Here's the breakdown across {num_rows} items."
        return f"Query returned {num_rows} result(s)."


# Singleton instance
llm_service = LLMService()
