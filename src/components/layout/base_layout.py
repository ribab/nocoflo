from abc import ABC, abstractmethod
from typing import Callable, Optional, Dict, List

class BaseLayout(ABC):
    """Abstract base class for layout components"""
    
    def __init__(self, content_func: Callable, table_id: Optional[int] = None):
        """
        Initialize the layout with content function and optional table ID
        
        Args:
            content_func: Function to render the main content
            table_id: Optional table ID for table-specific layouts
        """
        self.content_func = content_func
        self.table_id = table_id
    
    @abstractmethod
    def render(self) -> None:
        """Render the complete layout with navigation, headers, and content"""
        pass
    
    @abstractmethod
    def get_user_tables(self) -> List[Dict]:
        """
        Get available tables for navigation
        
        Returns:
            List of table metadata dictionaries
        """
        pass
    
    @abstractmethod
    def show_table_menu(self, table: Dict) -> None:
        """
        Display table-specific menu
        
        Args:
            table: Table metadata dictionary
        """
        pass 