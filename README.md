# Business Analytics Chatbot

A production-ready natural language to SQL query system for business analytics. Users can ask questions in plain English and get SQL queries, results, explanations, and visualizations.

## Architecture

```
User Question (NL)
      ↓
LLM (SQL Generator with strict prompt)
      ↓
SQL Validator (VERY IMPORTANT - Security)
      ↓
Database (PostgreSQL / SQLite)
      ↓
Result
      ↓
LLM (optional: explanation)
      ↓
Visualization (Chart)
```

## Features

- **Natural Language to SQL**: Convert plain English questions to SQL queries
- **SQL Validation**: Critical security layer to prevent SQL injection
- **Database Support**: SQLite (default) and PostgreSQL
- **Result Processing**: Automatic formatting and data processing
- **LLM Explanations**: Optional natural language explanations of results
- **Data Visualization**: Automatic chart generation (bar, line, pie, scatter)
- **Interactive Mode**: Chat-like interface for querying data

## Database Schema

The system uses a normalized 3NF schema with 4 tables:

- **users**: Customer information (id, name, email, created_at, country)
- **products**: Product catalog (id, name, category, price)
- **orders**: Order headers (id, user_id, order_date, total_amount)
- **order_items**: Order line items (id, order_id, product_id, quantity, price)

## Installation

### Prerequisites

- Python 3.8+
- pip

### Setup

1. Clone or navigate to the project directory:
```bash
cd analytics_chatbot_db
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Optional: LLM API Keys

For enhanced SQL generation and natural language explanations, set up API keys:

**OpenAI (recommended):**
```bash
export OPENAI_API_KEY='your-openai-api-key'
```

**Anthropic:**
```bash
export ANTHROPIC_API_KEY='your-anthropic-api-key'
```

Without API keys, the system uses mock mode with pattern matching.

## Usage

### Initial Setup

First, set up the database with schema and seed data:

```bash
python app.py --setup
```

This creates:
- SQLite database (`analytics.db`)
- Tables with proper indexes and constraints
- Seed data (12 users, 15 products, 12 orders, 30 order items)

### Interactive Mode

Run the chatbot in interactive mode:

```bash
python app.py
```

Example questions:
- "Show me all users"
- "How many products do we have?"
- "What is the total revenue from orders?"
- "Count users by country"
- "Show me recent orders"
- "What are the products by category?"

### Single Question Mode

Ask a single question and exit:

```bash
python app.py --question "Show me all users from USA"
```

### PostgreSQL Mode

Use PostgreSQL instead of SQLite:

```bash
python app.py --db-type postgresql --db-path "your_database_name"
```

Note: For PostgreSQL, you'll need to set up environment variables or modify the connection parameters in `app.py`.

### Disable Features

Disable LLM explanations:
```bash
python app.py --no-explanation
```

Disable chart generation:
```bash
python app.py --no-visualization
```

## Project Structure

```
analytics_chatbot_db/
├── app.py                      # Main application entry point
├── sql_generator.py            # LLM integration for SQL generation
├── sql_validator.py            # SQL validation (security layer)
├── database_connector.py       # Database connector (SQLite/PostgreSQL)
├── result_processor.py         # Result processing and explanations
├── visualizer.py               # Chart generation
├── schema.sql                  # Database schema
├── seed_data.sql               # Seed data
├── sql_generator_prompt.txt    # LLM prompt template
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Security Features

The SQL Validator is a critical security component that:

- **Blocks dangerous operations**: DELETE, UPDATE, INSERT, DROP, etc.
- **Detects SQL injection**: Suspicious patterns like `; DROP TABLE`, `1=1`, etc.
- **Enforces LIMIT clauses**: Prevents large result sets
- **Validates table names**: Only allows whitelisted tables
- **Syntax validation**: Uses sqlparse for SQL syntax checking

## Example Output

```
============================================================
Question: Count users by country
============================================================

✓ Query executed successfully
📊 Rows returned: 4

SQL Query:
  SELECT country, COUNT(*) as user_count FROM users GROUP BY country LIMIT 100

💡 Explanation: The query returned 4 result(s). The data shows user distribution across countries.

📋 Results:
Columns: country, user_count
  Row 1: {'country': 'USA', 'user_count': 4}
  Row 2: {'country': 'UK', 'user_count': 2}
  Row 3: {'country': 'Canada', 'user_count': 2}
  Row 4: {'country': 'Australia', 'user_count': 2}

📈 Visualization: Generated (base64 encoded)
============================================================
```

## Components

### SQL Generator (`sql_generator.py`)
- Converts natural language to SQL using LLM
- Supports OpenAI and Anthropic APIs
- Falls back to pattern matching without API keys

### SQL Validator (`sql_validator.py`)
- **CRITICAL SECURITY COMPONENT**
- Validates SQL before execution
- Prevents SQL injection and unauthorized operations
- Enforces safety rules

### Database Connector (`database_connector.py`)
- Supports SQLite and PostgreSQL
- Connection management
- Query execution
- Schema loading

### Result Processor (`result_processor.py`)
- Processes query results
- Generates natural language explanations
- Formats data for display

### Visualizer (`visualizer.py`)
- Auto-detects best chart type
- Supports bar, line, pie, scatter charts
- Exports as base64 encoded images

## Development

### Running Tests

Test individual components:

```bash
# Test SQL Validator
python sql_validator.py

# Test Database Connector
python database_connector.py

# Test SQL Generator
python sql_generator.py

# Test Result Processor
python result_processor.py

# Test Visualizer
python visualizer.py
```

### Adding New Tables

1. Update `schema.sql` with new table definitions
2. Update `seed_data.sql` with seed data
3. Update `sql_validator.py` to add new table to `ALLOWED_TABLES`
4. Update `sql_generator_prompt.txt` with new schema

## License

MIT License

## Contributing

Contributions welcome! Please ensure:
- All SQL queries pass validation
- Security rules are followed
- Code is well-documented
- Tests pass for all components
