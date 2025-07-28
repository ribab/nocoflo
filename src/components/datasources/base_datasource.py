from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Any, Literal, Union, Optional, Type
from pydantic import BaseModel, Field, root_validator
import pandas as pd
from pluggy import HookspecMarker

# =========================
# Pydantic Configuration Models
# =========================

class BaseDataSourceConfig(BaseModel):
    """Base configuration for all datasources"""
    table_name: str = Field(..., description="Name of the table to operate on")

# =========================
# Query & Filter Schema
# =========================

class Condition(BaseModel):
    field: str
    op: Literal['=', '!=', '<', '<=', '>', '>=', 'in']
    value: object

class ConditionList(BaseModel):
    mode: Literal['AND', 'OR']
    filters: List['ConditionUnion']

    @root_validator(pre=True)
    def ensure_non_empty(cls, values):
        flt = values.get('filters')
        if not flt or not isinstance(flt, list):
            raise ValueError("`filters` must be a non-empty list")
        return values

ConditionUnion = Union[Condition, ConditionList]

class OrderItem(BaseModel):
    field: str
    ascending: bool = True

class QuerySpec(BaseModel):
    limit: Optional[int] = Field(None, ge=1)
    offset: int = Field(0, ge=0)
    order_by: Optional[List[OrderItem]] = None
    filter: Optional[ConditionUnion] = None

class InsertSpec(BaseModel):
    payload: dict[str, Any]

class UpdateSpec(BaseModel):
    filters: ConditionUnion
    payload: dict[str, Any]

class DeleteSpec(BaseModel):
    filters: ConditionUnion

# =========================
# Pluggy Hook Specifications
# =========================

hookspec = HookspecMarker("datasource")

@hookspec
def connect(config) -> Any:
    """Open a datasource connection."""
    pass

@hookspec
def read(conn, query: QuerySpec) -> pd.DataFrame:
    """Read data from datasource."""
    pass

@hookspec
def insert(conn, data: InsertSpec) -> int:
    """Insert data into datasource."""
    pass

@hookspec
def update(conn, spec: UpdateSpec) -> int:
    """Update data in datasource."""
    pass

@hookspec
def delete(conn, spec: DeleteSpec) -> int:
    """Delete data from datasource."""
    pass

@hookspec
def get_table_data(table_config: dict, limit: int = 100) -> tuple:
    """Get table data with backward compatibility."""
    pass

@hookspec
def update_cell(table_config: dict, pk_col: str, pk_value: str, column: str, new_value):
    """Update a single cell in the table."""
    pass

@hookspec
def insert_row(table_config: dict, data: dict):
    """Insert a row into the table."""
    pass

@hookspec
def delete_row(table_config: dict, pk_col: str, pk_value: str):
    """Delete a row from the table."""
    pass

@hookspec
def get_schema(table_config: dict):
    """Get table schema."""
    pass

@hookspec
def test_connection(connection_config: dict):
    """Test connection to datasource."""
    pass

class BaseDatasource(ABC):
    """Abstract base class for datasource plugins"""
    
    @abstractmethod
    def connect(self, config) -> Any:
        """Open a datasource connection."""
        pass
    
    @abstractmethod
    def read(self, conn, query: QuerySpec) -> pd.DataFrame:
        """Read data from datasource."""
        pass
    
    @abstractmethod
    def insert(self, conn, data: InsertSpec) -> int:
        """Insert data into datasource."""
        pass
    
    @abstractmethod
    def update(self, conn, spec: UpdateSpec) -> int:
        """Update data in datasource."""
        pass
    
    @abstractmethod
    def delete(self, conn, spec: DeleteSpec) -> int:
        """Delete data from datasource."""
        pass
    
    @abstractmethod
    def get_table_data(self, table_config: dict, limit: int = 100) -> tuple:
        """Get table data with backward compatibility."""
        pass
    
    @abstractmethod
    def update_cell(self, table_config: dict, pk_col: str, pk_value: str, column: str, new_value):
        """Update a single cell in the table."""
        pass
    
    @abstractmethod
    def insert_row(self, table_config: dict, data: dict):
        """Insert a row into the table."""
        pass
    
    @abstractmethod
    def delete_row(self, table_config: dict, pk_col: str, pk_value: str):
        """Delete a row from the table."""
        pass
    
    @abstractmethod
    def get_schema(self, table_config: dict):
        """Get table schema."""
        pass
    
    @abstractmethod
    def test_connection(self, connection_config: dict):
        """Test connection to datasource."""
        pass
