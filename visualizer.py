"""
Visualization Component
Creates charts and visualizations from query results.
"""

import matplotlib.pyplot as plt
import matplotlib
from typing import Dict, Any, List, Optional
import logging
import io
import base64

# Use non-interactive backend for server environments
matplotlib.use('Agg')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataVisualizer:
    """Creates visualizations from query results."""
    
    def __init__(self, style: str = 'seaborn-v0_8-darkgrid'):
        """
        Initialize visualizer.
        
        Args:
            style: Matplotlib style to use
        """
        try:
            plt.style.use(style)
        except:
            plt.style.use('default')
            logger.warning(f"Style '{style}' not available, using default")
    
    def visualize(
        self, 
        processed: Dict[str, Any], 
        chart_type: Optional[str] = None
    ) -> Optional[str]:
        """
        Create a visualization from processed query results.
        
        Args:
            processed: Processed result dictionary from ResultProcessor
            chart_type: Type of chart ('bar', 'line', 'pie', 'scatter'). 
                       Auto-detected if not specified.
            
        Returns:
            Base64 encoded image string or None if visualization not possible
        """
        if not processed['success'] or not processed['data']:
            logger.info("No data to visualize")
            return None
        
        data = processed['data']
        columns = processed['columns']
        
        # Auto-detect chart type if not specified
        if chart_type is None:
            chart_type = self._detect_chart_type(data, columns)
        
        try:
            if chart_type == 'bar':
                return self._create_bar_chart(data, columns)
            elif chart_type == 'line':
                return self._create_line_chart(data, columns)
            elif chart_type == 'pie':
                return self._create_pie_chart(data, columns)
            elif chart_type == 'scatter':
                return self._create_scatter_chart(data, columns)
            else:
                logger.warning(f"Unsupported chart type: {chart_type}")
                return None
                
        except Exception as e:
            logger.error(f"Visualization failed: {str(e)}")
            return None
    
    def _detect_chart_type(self, data: List[Dict], columns: List[str]) -> str:
        """
        Auto-detect the best chart type based on data structure.
        
        Args:
            data: Query result data
            columns: Column names
            
        Returns:
            Detected chart type
        """
        if len(data) == 0:
            return 'bar'
        
        # Check for categorical data (good for bar/pie)
        if len(columns) == 2:
            # First column as labels, second as values
            first_col_type = self._detect_column_type(data, columns[0])
            second_col_type = self._detect_column_type(data, columns[1])
            
            if first_col_type == 'string' and second_col_type == 'numeric':
                # Categorical with numeric values - good for bar or pie
                if len(data) <= 10:
                    return 'pie'  # Pie for small number of categories
                else:
                    return 'bar'  # Bar for many categories
            
            elif first_col_type == 'numeric' and second_col_type == 'numeric':
                return 'scatter'  # Two numeric columns - scatter plot
        
        # Check for time series (good for line)
        if any('date' in col.lower() or 'time' in col.lower() for col in columns):
            return 'line'
        
        # Default to bar chart
        return 'bar'
    
    def _detect_column_type(self, data: List[Dict], column: str) -> str:
        """Detect if a column is numeric or string."""
        if not data:
            return 'string'
        
        # Check first non-null value
        for row in data:
            value = row.get(column)
            if value is not None:
                if isinstance(value, (int, float)):
                    return 'numeric'
                else:
                    try:
                        float(value)
                        return 'numeric'
                    except (ValueError, TypeError):
                        return 'string'
        
        return 'string'
    
    def _create_bar_chart(self, data: List[Dict], columns: List[str]) -> str:
        """Create a bar chart."""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        if len(columns) >= 2:
            labels = [str(row[columns[0]]) for row in data]
            values = [float(row[columns[1]]) for row in data]
            
            bars = ax.bar(labels, values, color='steelblue', edgecolor='navy', alpha=0.7)
            ax.set_xlabel(columns[0])
            ax.set_ylabel(columns[1])
            
            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.1f}',
                       ha='center', va='bottom', fontsize=9)
        else:
            # Single column - count occurrences
            labels = [str(row[columns[0]]) for row in data]
            ax.bar(range(len(labels)), [1] * len(labels))
            ax.set_xticks(range(len(labels)))
            ax.set_xticklabels(labels, rotation=45, ha='right')
        
        ax.set_title('Bar Chart')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        return self._fig_to_base64(fig)
    
    def _create_line_chart(self, data: List[Dict], columns: List[str]) -> str:
        """Create a line chart."""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        if len(columns) >= 2:
            x_values = [row[columns[0]] for row in data]
            y_values = [float(row[columns[1]]) for row in data]
            
            ax.plot(x_values, y_values, marker='o', linewidth=2, markersize=6, 
                   color='steelblue', markerfacecolor='navy')
            ax.set_xlabel(columns[0])
            ax.set_ylabel(columns[1])
        else:
            ax.plot(range(len(data)), [1] * len(data), marker='o')
        
        ax.set_title('Line Chart')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        return self._fig_to_base64(fig)
    
    def _create_pie_chart(self, data: List[Dict], columns: List[str]) -> str:
        """Create a pie chart."""
        fig, ax = plt.subplots(figsize=(8, 8))
        
        if len(columns) >= 2:
            labels = [str(row[columns[0]]) for row in data]
            values = [float(row[columns[1]]) for row in data]
        else:
            labels = [str(row[columns[0]]) for row in data]
            values = [1] * len(data)
        
        colors = plt.cm.Set3(range(len(labels)))
        wedges, texts, autotexts = ax.pie(
            values, 
            labels=labels, 
            autopct='%1.1f%%',
            colors=colors,
            startangle=90
        )
        
        # Improve text readability
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        ax.set_title('Pie Chart')
        plt.tight_layout()
        
        return self._fig_to_base64(fig)
    
    def _create_scatter_chart(self, data: List[Dict], columns: List[str]) -> str:
        """Create a scatter plot."""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        if len(columns) >= 2:
            x_values = [float(row[columns[0]]) for row in data]
            y_values = [float(row[columns[1]]) for row in data]
            
            ax.scatter(x_values, y_values, alpha=0.6, s=100, 
                      c='steelblue', edgecolors='navy', linewidth=1.5)
            ax.set_xlabel(columns[0])
            ax.set_ylabel(columns[1])
        else:
            ax.scatter(range(len(data)), [1] * len(data))
        
        ax.set_title('Scatter Plot')
        plt.tight_layout()
        
        return self._fig_to_base64(fig)
    
    def _fig_to_base64(self, fig) -> str:
        """Convert matplotlib figure to base64 string."""
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
        return img_str
    
    def save_chart(self, img_base64: str, filename: str):
        """
        Save base64 encoded image to file.
        
        Args:
            img_base64: Base64 encoded image string
            filename: Output filename
        """
        img_data = base64.b64decode(img_base64)
        with open(filename, 'wb') as f:
            f.write(img_data)
        logger.info(f"Chart saved to {filename}")


# Example usage
if __name__ == "__main__":
    visualizer = DataVisualizer()
    
    # Test data
    test_data = {
        'success': True,
        'row_count': 5,
        'columns': ['category', 'count'],
        'data': [
            {'category': 'Electronics', 'count': 15},
            {'category': 'Furniture', 'count': 8},
            {'category': 'Stationery', 'count': 12},
            {'category': 'Books', 'count': 5},
            {'category': 'Accessories', 'count': 10}
        ]
    }
    
    # Create visualization
    img = visualizer.visualize(test_data, chart_type='bar')
    
    if img:
        print("Visualization created successfully!")
        print(f"Image length: {len(img)} characters")
        
        # Save to file
        visualizer.save_chart(img, 'test_chart.png')
        print("Chart saved to test_chart.png")
    else:
        print("Failed to create visualization")
