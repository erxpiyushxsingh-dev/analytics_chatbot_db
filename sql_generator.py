"""
SQL Generator LLM Integration
Converts natural language questions to SQL queries using LLM.
"""

import os
from typing import Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SQLGenerator:
    """Generates SQL queries from natural language using LLM."""
    
    def __init__(self, prompt_template_path: str = 'sql_generator_prompt.txt'):
        """
        Initialize SQL Generator.
        
        Args:
            prompt_template_path: Path to the prompt template file
        """
        self.prompt_template_path = prompt_template_path
        self.prompt_template = self._load_prompt_template()
        self.api_key = os.getenv('OPENAI_API_KEY') or os.getenv('ANTHROPIC_API_KEY')
        
        if not self.api_key:
            logger.warning(
                "No API key found. Set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable. "
                "Using mock mode for testing."
            )
    
    def _load_prompt_template(self) -> str:
        """Load the prompt template from file."""
        try:
            with open(self.prompt_template_path, 'r') as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"Prompt template not found: {self.prompt_template_path}")
            # Return a default template
            return """
You are an expert SQL generator.
Convert the user's natural language question into a PostgreSQL SQL query.
Rules:
- ONLY generate SELECT queries
- NEVER use DELETE, UPDATE, INSERT
- Always include LIMIT 100
- Use table names: users, products, orders, order_items
User Question: {user_input}
Output: SQL query only.
"""
    
    def generate_sql(self, user_question: str) -> Optional[str]:
        """
        Generate SQL query from natural language question.
        
        Args:
            user_question: Natural language question from user
            
        Returns:
            Generated SQL query or None if generation fails
        """
        # Format the prompt with user question
        prompt = self.prompt_template.replace('{user_input}', user_question)
        
        # Try to use actual LLM if API key is available
        if self.api_key:
            return self._generate_with_llm(prompt)
        else:
            # Use mock mode for testing without API key
            return self._generate_mock(user_question)
    
    def _generate_with_llm(self, prompt: str) -> Optional[str]:
        """
        Generate SQL using actual LLM API.
        
        Args:
            prompt: Formatted prompt
            
        Returns:
            Generated SQL query or None
        """
        try:
            # Try OpenAI first
            if os.getenv('OPENAI_API_KEY'):
                return self._generate_with_openai(prompt)
            # Try Anthropic second
            elif os.getenv('ANTHROPIC_API_KEY'):
                return self._generate_with_anthropic(prompt)
            else:
                logger.warning("No API key configured, using mock mode")
                return None
                
        except Exception as e:
            logger.error(f"LLM generation failed: {str(e)}")
            return None
    
    def _generate_with_openai(self, prompt: str) -> Optional[str]:
        """Generate SQL using OpenAI API."""
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert SQL generator. Output only SQL queries, no explanations."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0,
                max_tokens=500
            )
            
            sql_query = response.choices[0].message.content.strip()
            logger.info(f"Generated SQL with OpenAI: {sql_query}")
            return sql_query
            
        except ImportError:
            logger.error("OpenAI library not installed. Install with: pip install openai")
            return None
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            return None
    
    def _generate_with_anthropic(self, prompt: str) -> Optional[str]:
        """Generate SQL using Anthropic API."""
        try:
            import anthropic
            
            client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
            
            response = client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=500,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            sql_query = response.content[0].text.strip()
            logger.info(f"Generated SQL with Anthropic: {sql_query}")
            return sql_query
            
        except ImportError:
            logger.error("Anthropic library not installed. Install with: pip install anthropic")
            return None
        except Exception as e:
            logger.error(f"Anthropic API error: {str(e)}")
            return None
    
    def _generate_mock(self, user_question: str) -> Optional[str]:
        """
        Mock SQL generator for testing without API keys.
        Uses simple pattern matching to generate basic queries.
        
        Args:
            user_question: Natural language question
            
        Returns:
            Generated SQL query or None
        """
        question_lower = user_question.lower()
        
        # Simple pattern matching for common queries
        if 'user' in question_lower and 'count' in question_lower:
            return "SELECT COUNT(*) as user_count FROM users LIMIT 100"
        
        elif 'product' in question_lower and 'count' in question_lower:
            return "SELECT COUNT(*) as product_count FROM products LIMIT 100"
        
        elif 'order' in question_lower and 'count' in question_lower:
            return "SELECT COUNT(*) as order_count FROM orders LIMIT 100"
        
        elif 'user' in question_lower:
            return "SELECT * FROM users LIMIT 100"
        
        elif 'product' in question_lower:
            return "SELECT * FROM products LIMIT 100"
        
        elif 'order' in question_lower:
            return "SELECT * FROM orders LIMIT 100"
        
        elif 'revenue' in question_lower or 'total' in question_lower:
            return "SELECT SUM(total_amount) as total_revenue FROM orders LIMIT 100"
        
        elif 'country' in question_lower:
            return "SELECT country, COUNT(*) as user_count FROM users GROUP BY country LIMIT 100"
        
        elif 'category' in question_lower:
            return "SELECT category, COUNT(*) as product_count FROM products GROUP BY category LIMIT 100"
        
        else:
            # Default fallback
            return "SELECT * FROM users LIMIT 10"


# Example usage
if __name__ == "__main__":
    generator = SQLGenerator()
    
    # Test questions
    test_questions = [
        "Show me all users",
        "How many products do we have?",
        "What is the total revenue from orders?",
        "Count users by country",
        "Show me recent orders",
    ]
    
    for question in test_questions:
        print(f"\nQuestion: {question}")
        sql = generator.generate_sql(question)
        print(f"Generated SQL: {sql}")
