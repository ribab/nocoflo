from abc import ABC, abstractmethod
from typing import Dict, List, Any

class BaseView(ABC):
    """Abstract base class for all view types (table, chart, form, etc.)"""
    
    def __init__(self, table_id: int, datasource: 'BaseDatasource'):
        """
        Initialize the view with table ID and datasource
        
        Args:
            table_id: The ID of the table to display
            datasource: The datasource to use for data access
        """
        self.table_id = table_id
        self.datasource = datasource
    
    @abstractmethod
    def render(self) -> None:
        """Render the view with data from the datasource"""
        pass
    
    @abstractmethod
    def get_view_name(self) -> str:
        """Return human-readable view name"""
        pass
    
    @abstractmethod
    def can_handle_table(self, table_meta: Dict) -> bool:
        """
        Determine if this view is appropriate for the given table
        
        Args:
            table_meta: Table metadata dictionary
            
        Returns:
            True if this view can handle the table, False otherwise
        """
        pass
    
    @abstractmethod
    def get_priority(self) -> int:
        """
        Return selection priority (higher = preferred)
        
        Returns:
            Priority value where higher numbers indicate higher preference
        """
        pass 