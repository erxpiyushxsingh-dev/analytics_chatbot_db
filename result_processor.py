"""
Result Processor and Explanation LLM
Processes query results and generates optional natural language explanations.
"""

import os
from typing import Optional, Dict, Any, List
import logging
from database_connector import QueryResult

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ResultProcessor:
    """Processes query results and generates explanations."""
    
    def __init__(self, enable_explanation: bool = True):
        """
        Initialize Result Processor.
        
        Args:
            enable_explanation: Whether to generate LLM explanations
        """
        self.enable_explanation = enable_explanation
        self.api_key = os.getenv('OPENAI_API_KEY') or os.getenv('ANTHROPIC_API_KEY')
        
        if not self.api_key and enable_explanation:
            logger.warning(
                "No API key found. Explanations will use simple templates instead of LLM."
            )
    
    def process_result(
        self, 
        query: str, 
        result: QueryResult, 
        user_question: str
    ) -> Dict[str, Any]:
        """
        Process query result into a structured format.
        
        Args:
            query: The SQL query that was executed
            result: QueryResult from database
            user_question: Original natural language question
            
        Returns:
            Dictionary with processed result data
        """
        processed = {
            'success': result.success,
            'query': query,
            'user_question': user_question,
            'row_count': result.row_count,
            'columns': result.columns,
            'data': self._rows_to_dict(result),
            'error': result.error,
            'explanation': None
        }
        
        # Generate explanation if enabled and result is successful
        if self.enable_explanation and result.success:
            processed['explanation'] = self.generate_explanation(
                user_question, 
                query, 
                result
            )
        
        return processed
    
    def _rows_to_dict(self, result: QueryResult) -> List[Dict[str, Any]]:
        """Convert result rows to list of dictionaries."""
        if not result.success or not result.rows:
            return []
        
        return [
            {col: val for col, val in zip(result.columns, row)}
            for row in result.rows
        ]
    
    def generate_explanation(
        self, 
        user_question: str, 
        query: str, 
        result: QueryResult
    ) -> str:
        """
        Generate natural language explanation of the query result.
        
        Args:
            user_question: Original question
            query: SQL query executed
            result: Query result
            
        Returns:
            Natural language explanation
        """
        if self.api_key:
            return self._generate_with_llm(user_question, query, result)
        else:
            return self._generate_template_explanation(user_question, query, result)
    
    def _generate_with_llm(
        self, 
        user_question: str, 
        query: str, 
        result: QueryResult
    ) -> str:
        """Generate explanation using LLM."""
        try:
            # Try OpenAI first
            if os.getenv('OPENAI_API_KEY'):
                return self._explain_with_openai(user_question, query, result)
            # Try Anthropic second
            elif os.getenv('ANTHROPIC_API_KEY'):
                return self._explain_with_anthropic(user_question, query, result)
            else:
                return self._generate_template_explanation(user_question, query, result)
                
        except Exception as e:
            logger.error(f"LLM explanation failed: {str(e)}")
            return self._generate_template_explanation(user_question, query, result)
    
    def _explain_with_openai(
        self, 
        user_question: str, 
        query: str, 
        result: QueryResult
    ) -> str:
        """Generate explanation using OpenAI."""
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            
            # Prepare result summary
            result_summary = self._summarize_result(result)
            
            prompt = f"""
User Question: {user_question}
SQL Query: {query}
Result: {result_summary}

Provide a brief, clear explanation of what this data shows in 1-2 sentences.
"""
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful data analyst assistant. Explain query results clearly and concisely."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.5,
                max_tokens=200
            )
            
            explanation = response.choices[0].message.content.strip()
            logger.info(f"Generated explanation with OpenAI")
            return explanation
            
        except Exception as e:
            logger.error(f"OpenAI explanation error: {str(e)}")
            return self._generate_template_explanation(user_question, query, result)
    
    def _explain_with_anthropic(
        self, 
        user_question: str, 
        query: str, 
        result: QueryResult
    ) -> str:
        """Generate explanation using Anthropic."""
        try:
            import anthropic
            
            client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
            
            result_summary = self._summarize_result(result)
            
            prompt = f"""
User Question: {user_question}
SQL Query: {query}
Result: {result_summary}

Provide a brief, clear explanation of what this data shows in 1-2 sentences.
"""
            
            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=200,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            explanation = response.content[0].text.strip()
            logger.info(f"Generated explanation with Anthropic")
            return explanation
            
        except Exception as e:
            logger.error(f"Anthropic explanation error: {str(e)}")
            return self._generate_template_explanation(user_question, query, result)
    
    def _summarize_result(self, result: QueryResult) -> str:
        """Create a text summary of the result for LLM context."""
        if not result.success:
            return f"Query failed: {result.error}"
        
        if result.row_count == 0:
            return "No results found."
        
        # Show first few rows as sample
        sample_rows = min(3, result.row_count)
        summary = f"Returned {result.row_count} rows. Columns: {result.columns}. "
        summary += f"Sample data: "
        
        for i in range(sample_rows):
            row_dict = {col: val for col, val in zip(result.columns, result.rows[i])}
            summary += f"Row {i+1}: {row_dict}. "
        
        return summary
    
    def _generate_template_explanation(
        self, 
        user_question: str, 
        query: str, 
        result: QueryResult
    ) -> str:
        """Generate explanation using simple templates (fallback)."""
        if not result.success:
            return f"Query failed: {result.error}"
        
        if result.row_count == 0:
            return "No results found for your query."
        
        # Simple template-based explanations
        question_lower = user_question.lower()
        
        if 'count' in question_lower:
            if result.rows and result.row_count > 0:
                value = result.rows[0][0] if len(result.rows[0]) > 0 else 0
                return f"The query returned {result.row_count} result(s). The count is {value}."
        
        elif 'total' in question_lower or 'sum' in question_lower or 'revenue' in question_lower:
            if result.rows and result.row_count > 0:
                value = result.rows[0][0] if len(result.rows[0]) > 0 else 0
                return f"The total is {value}."
        
        elif 'average' in question_lower or 'avg' in question_lower:
            if result.rows and result.row_count > 0:
                value = result.rows[0][0] if len(result.rows[0]) > 0 else 0
                return f"The average is {value}."
        
        # Generic explanation
        return f"Query completed successfully and returned {result.row_count} row(s)."
    
    def format_for_display(self, processed: Dict[str, Any]) -> str:
        """
        Format processed result for display.
        
        Args:
            processed: Processed result dictionary
            
        Returns:
            Formatted string
        """
        output = []
        
        if not processed['success']:
            output.append(f"❌ Error: {processed['error']}")
            return '\n'.join(output)
        
        output.append(f"✓ Query executed successfully")
        output.append(f"📊 Rows returned: {processed['row_count']}")
        
        if processed['explanation']:
            output.append(f"\n💡 Explanation: {processed['explanation']}")
        
        if processed['data']:
            output.append(f"\n📋 Results:")
            output.append(f"Columns: {', '.join(processed['columns'])}")
            
            # Show first 5 rows
            for i, row in enumerate(processed['data'][:5]):
                output.append(f"  Row {i+1}: {row}")
            
            if processed['row_count'] > 5:
                output.append(f"  ... and {processed['row_count'] - 5} more rows")
        
        return '\n'.join(output)


# Example usage
if __name__ == "__main__":
    from database_connector import DatabaseConnector
    
    processor = ResultProcessor(enable_explanation=False)  # Use template mode for testing
    
    # Create a mock result
    mock_result = QueryResult(
        columns=['name', 'email', 'country'],
        rows=[
            ('John Smith', 'john@email.com', 'USA'),
            ('Emma Johnson', 'emma@email.com', 'UK'),
            ('Michael Chen', 'michael@email.com', 'Canada')
        ],
        row_count=3,
        success=True
    )
    
    processed = processor.process_result(
        query="SELECT name, email, country FROM users LIMIT 10",
        result=mock_result,
        user_question="Show me all users"
    )
    
    print(processor.format_for_display(processed))
