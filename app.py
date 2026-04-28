"""
Main Application Entry Point
Business Analytics Chatbot - Natural Language to SQL

Architecture:
User Question (NL) → LLM (SQL Generator) → SQL Validator → Database → Result → LLM (Explanation) → Visualization
"""

import os
import sys
import logging
from typing import Optional

from sql_generator import SQLGenerator
from sql_validator import SQLValidator
from database_connector import DatabaseConnector
from result_processor import ResultProcessor
from visualizer import DataVisualizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AnalyticsChatbot:
    """Main analytics chatbot application."""
    
    def __init__(
        self, 
        db_type: str = 'sqlite',
        db_path: str = 'analytics.db',
        enable_explanation: bool = True,
        enable_visualization: bool = True
    ):
        """
        Initialize the analytics chatbot.
        
        Args:
            db_type: 'sqlite' or 'postgresql'
            db_path: Path to SQLite database (if using SQLite)
            enable_explanation: Enable LLM explanations
            enable_visualization: Enable chart generation
        """
        logger.info("Initializing Analytics Chatbot...")
        
        # Initialize components
        self.sql_generator = SQLGenerator()
        self.sql_validator = SQLValidator()
        self.result_processor = ResultProcessor(enable_explanation=enable_explanation)
        self.visualizer = DataVisualizer() if enable_visualization else None
        self.enable_visualization = enable_visualization
        
        # Initialize database
        db_kwargs = {'db_path': db_path} if db_type == 'sqlite' else {}
        self.db = DatabaseConnector(db_type, **db_kwargs)
        
        # Connect to database
        if not self.db.connect():
            logger.error("Failed to connect to database")
            raise Exception("Database connection failed")
        
        logger.info("Analytics Chatbot initialized successfully")
    
    def query(self, user_question: str) -> dict:
        """
        Process a natural language question and return results.
        
        Args:
            user_question: Natural language question from user
            
        Returns:
            Dictionary with query results, explanation, and visualization
        """
        logger.info(f"Processing question: {user_question}")
        
        result = {
            'question': user_question,
            'success': False,
            'sql': None,
            'data': None,
            'explanation': None,
            'visualization': None,
            'error': None
        }
        
        try:
            # Step 1: Generate SQL from natural language
            logger.info("Step 1: Generating SQL...")
            sql = self.sql_generator.generate_sql(user_question)
            
            if not sql:
                result['error'] = "Failed to generate SQL query"
                return result
            
            result['sql'] = sql
            logger.info(f"Generated SQL: {sql}")
            
            # Step 2: Validate SQL (CRITICAL SECURITY STEP)
            logger.info("Step 2: Validating SQL...")
            is_valid, validation_errors = self.sql_validator.validate(sql)
            
            if not is_valid:
                error_msg = "SQL validation failed: " + "; ".join(validation_errors)
                logger.error(error_msg)
                result['error'] = error_msg
                return result
            
            logger.info("SQL validation passed")
            
            # Step 3: Execute query on database
            logger.info("Step 3: Executing query...")
            query_result = self.db.execute_query(sql)
            
            if not query_result.success:
                result['error'] = f"Query execution failed: {query_result.error}"
                return result
            
            # Step 4: Process results and generate explanation
            logger.info("Step 4: Processing results...")
            processed = self.result_processor.process_result(
                query=sql,
                result=query_result,
                user_question=user_question
            )
            
            result['success'] = True
            result['data'] = processed['data']
            result['row_count'] = processed['row_count']
            result['columns'] = processed['columns']
            result['explanation'] = processed['explanation']
            
            # Step 5: Generate visualization (if enabled and data available)
            if self.enable_visualization and processed['row_count'] > 0:
                logger.info("Step 5: Generating visualization...")
                viz = self.visualizer.visualize(processed)
                result['visualization'] = viz
            
            logger.info("Query processed successfully")
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            result['error'] = str(e)
        
        return result
    
    def format_response(self, result: dict) -> str:
        """
        Format the query result for display.
        
        Args:
            result: Query result dictionary
            
        Returns:
            Formatted string
        """
        output = []
        
        output.append("=" * 60)
        output.append(f"Question: {result['question']}")
        output.append("=" * 60)
        
        if not result['success']:
            output.append(f"\n❌ Error: {result['error']}")
            return '\n'.join(output)
        
        output.append(f"\n✓ Query executed successfully")
        output.append(f"📊 Rows returned: {result['row_count']}")
        output.append(f"\nSQL Query:")
        output.append(f"  {result['sql']}")
        
        if result['explanation']:
            output.append(f"\n💡 Explanation: {result['explanation']}")
        
        if result['data']:
            output.append(f"\n📋 Results:")
            output.append(f"Columns: {', '.join(result['columns'])}")
            
            # Show first 5 rows
            for i, row in enumerate(result['data'][:5]):
                output.append(f"  Row {i+1}: {row}")
            
            if result['row_count'] > 5:
                output.append(f"  ... and {result['row_count'] - 5} more rows")
        
        if result['visualization']:
            output.append(f"\n📈 Visualization: Generated (base64 encoded)")
        
        output.append("=" * 60)
        
        return '\n'.join(output)
    
    def interactive_mode(self):
        """Run the chatbot in interactive mode."""
        print("\n" + "=" * 60)
        print("Business Analytics Chatbot")
        print("Type your questions in natural language")
        print("Type 'quit' or 'exit' to stop")
        print("=" * 60 + "\n")
        
        while True:
            try:
                user_input = input("Your question: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("\nGoodbye!")
                    break
                
                result = self.query(user_input)
                print(self.format_response(result))
                print()
                
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"\nError: {str(e)}\n")
    
    def close(self):
        """Close database connection."""
        self.db.disconnect()
        logger.info("Chatbot closed")


def setup_database(db_connector: DatabaseConnector, schema_path: str = 'schema.sql', seed_path: str = 'seed_data.sql'):
    """
    Setup database with schema and seed data.
    
    Args:
        db_connector: DatabaseConnector instance
        schema_path: Path to schema SQL file
        seed_path: Path to seed data SQL file
    """
    logger.info("Setting up database...")
    
    # Execute schema
    if os.path.exists(schema_path):
        if db_connector.execute_script(schema_path):
            logger.info(f"Schema executed successfully: {schema_path}")
        else:
            logger.error(f"Failed to execute schema: {schema_path}")
    else:
        logger.warning(f"Schema file not found: {schema_path}")
    
    # Execute seed data
    if os.path.exists(seed_path):
        if db_connector.execute_script(seed_path):
            logger.info(f"Seed data executed successfully: {seed_path}")
        else:
            logger.error(f"Failed to execute seed data: {seed_path}")
    else:
        logger.warning(f"Seed data file not found: {seed_path}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Business Analytics Chatbot')
    parser.add_argument('--db-type', choices=['sqlite', 'postgresql'], default='sqlite',
                       help='Database type')
    parser.add_argument('--db-path', default='analytics.db',
                       help='SQLite database path')
    parser.add_argument('--setup', action='store_true',
                       help='Setup database with schema and seed data')
    parser.add_argument('--no-explanation', action='store_true',
                       help='Disable LLM explanations')
    parser.add_argument('--no-visualization', action='store_true',
                       help='Disable chart generation')
    parser.add_argument('--question', type=str,
                       help='Ask a single question and exit')
    
    args = parser.parse_args()
    
    try:
        # Initialize chatbot
        chatbot = AnalyticsChatbot(
            db_type=args.db_type,
            db_path=args.db_path,
            enable_explanation=not args.no_explanation,
            enable_visualization=not args.no_visualization
        )
        
        # Setup database if requested
        if args.setup:
            setup_database(chatbot.db)
        
        # Single question mode
        if args.question:
            result = chatbot.query(args.question)
            print(chatbot.format_response(result))
            
            # Save visualization if generated
            if result['visualization'] and chatbot.visualizer:
                chatbot.visualizer.save_chart(result['visualization'], 'chart.png')
                print("\nChart saved to chart.png")
        else:
            # Interactive mode
            chatbot.interactive_mode()
        
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        sys.exit(1)
    finally:
        if 'chatbot' in locals():
            chatbot.close()


if __name__ == "__main__":
    main()
