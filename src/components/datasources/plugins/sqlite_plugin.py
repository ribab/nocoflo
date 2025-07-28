from pluggy import HookimplMarker
import sqlite3
import pandas as pd
from pydantic import Field
from typing import Any, Dict, List, Tuple
from components.datasources.base_datasource import (
    BaseDatasource, QuerySpec, InsertSpec, UpdateSpec, DeleteSpec, 
    ConditionUnion, Condition, BaseDataSourceConfig
)

hookimpl = HookimplMarker("datasource")

class SQLiteConnectionWrapper:
    """Wrapper for SQLite connection that supports additional attributes."""
    
    def __init__(self, connection: sqlite3.Connection, table_name: str = None):
        self._connection = connection
        self._current_table = table_name or 'data'
    
    def __getattr__(self, name):
        """Delegate all other attributes to the underlying connection."""
        return getattr(self._connection, name)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._connection.close()

class SQLiteConfig(BaseDataSourceConfig):
    """SQLite configuration"""
    path: str = Field(..., description="Path to SQLite database file")

class SQLiteDataSource(BaseDatasource):
    name = "sqlite"

    @classmethod
    def get_config_class(cls):
        return SQLiteConfig

    @hookimpl
    def connect(self, config: SQLiteConfig):
        conn = sqlite3.connect(config.path)
        conn.row_factory = sqlite3.Row
        return SQLiteConnectionWrapper(conn, config.table_name)

    @hookimpl
    def insert(self, conn, data: InsertSpec):
        table = data.payload.pop("__table__")
        keys = ", ".join(data.payload.keys())
        placeholders = ", ".join(["?"] * len(data.payload))
        conn.execute(f"INSERT INTO {table} ({keys}) VALUES ({placeholders})", tuple(data.payload.values()))
        conn.commit()
        return 1

    @hookimpl
    def read(self, conn, query: QuerySpec):
        # Get table name from config or use default
        table = getattr(conn, '_current_table', 'data')
        
        # Basic SELECT * with optional WHERE/ORDER/LIMIT/OFFSET
        base_query = f"SELECT * FROM {table}"
        params = []
        
        if query.filter:
            where_clause, where_params = self._build_where(query.filter)
            base_query += f" WHERE {where_clause}"
            params.extend(where_params)
            
        if query.order_by:
            order_parts = [f"{o.field} {'ASC' if o.ascending else 'DESC'}" for o in query.order_by]
            base_query += " ORDER BY " + ", ".join(order_parts)
            
        if query.limit:
            base_query += f" LIMIT {query.limit}"
            
        if query.offset:
            base_query += f" OFFSET {query.offset}"
            
        cur = conn.execute(base_query, params)
        rows = cur.fetchall()
        
        if rows:
            return pd.DataFrame(rows, columns=[col[0] for col in cur.description])
        else:
            # Return empty DataFrame with correct columns
            cur.execute(f"PRAGMA table_info({table})")
            columns = [row[1] for row in cur.fetchall()]
            return pd.DataFrame(columns=columns)

    def _build_where(self, node: ConditionUnion):
        if isinstance(node, Condition):
            if node.op == 'in':
                placeholders = ', '.join(['?' for _ in node.value])
                return f"{node.field} IN ({placeholders})", list(node.value)
            else:
                return f"{node.field} {node.op} ?", [node.value]
        else:
            clauses = []
            all_params = []
            for sub in node.filters:
                sub_clause, sub_params = self._build_where(sub)
                clauses.append(f"({sub_clause})")
                all_params.extend(sub_params)
            connector = " AND " if node.mode == 'AND' else " OR "
            return connector.join(clauses), all_params

    @hookimpl
    def update(self, conn, spec: UpdateSpec):
        table = getattr(conn, '_current_table', 'data')
        set_clause = ", ".join([f"{k}=?" for k in spec.payload.keys()])
        where_clause, params = self._build_where(spec.filters)
        values = list(spec.payload.values()) + params
        cur = conn.execute(f"UPDATE {table} SET {set_clause} WHERE {where_clause}", values)
        conn.commit()
        return cur.rowcount

    @hookimpl
    def delete(self, conn, spec: DeleteSpec):
        table = getattr(conn, '_current_table', 'data')
        where_clause, params = self._build_where(spec.filters)
        cur = conn.execute(f"DELETE FROM {table} WHERE {where_clause}", params)
        conn.commit()
        return cur.rowcount

    # Legacy methods for backward compatibility
    @hookimpl
    def get_table_data(self, table_config: dict, limit: int = 100):
        """Legacy method for backward compatibility"""
        connection_string = table_config.get('connection_string')
        table_name = table_config.get('table_name')
        
        if not connection_string or not table_name:
            raise ValueError("connection_string and table_name are required")
        
        # Create config using the new structure
        config = self.create_config(connection_string, table_name)
        
        # Execute query
        conn = self.connect(config)
        df = self.read(conn, QuerySpec(limit=limit, offset=0))
        
        # Convert to tuple format for backward compatibility
        if df.empty:
            return [], []
        else:
            columns = df.columns.tolist()
            rows = [tuple(row) for row in df.values]
            return columns, rows

    @hookimpl
    def update_cell(self, table_config: dict, pk_col: str, pk_value: str, column: str, new_value):
        """Legacy method for backward compatibility"""
        connection_string = table_config.get('connection_string')
        table_name = table_config.get('table_name')
        
        if not connection_string or not table_name:
            return False
        
        try:
            config = self.create_config(connection_string, table_name)
            conn = self.connect(config)
            
            # Create update spec
            from ..base_datasource import Condition
            update_spec = UpdateSpec(
                filters=Condition(field=pk_col, op='=', value=pk_value),
                payload={column: new_value}
            )
            
            affected_rows = self.update(conn, update_spec)
            return affected_rows > 0
            
        except Exception as e:
            print(f"Error updating cell: {e}")
            return False

    @hookimpl
    def insert_row(self, table_config: dict, data: dict):
        """Legacy method for backward compatibility"""
        connection_string = table_config.get('connection_string')
        table_name = table_config.get('table_name')
        
        if not connection_string or not table_name:
            return False
        
        try:
            config = self.create_config(connection_string, table_name)
            conn = self.connect(config)
            
            # Add table name to payload
            data['__table__'] = table_name
            create_spec = CreateSpec(payload=data)
            
            affected_rows = self.create(conn, create_spec)
            return affected_rows > 0
            
        except Exception as e:
            print(f"Error inserting row: {e}")
            return False

    @hookimpl
    def delete_row(self, table_config: dict, pk_col: str, pk_value: str):
        """Legacy method for backward compatibility"""
        connection_string = table_config.get('connection_string')
        table_name = table_config.get('table_name')
        
        if not connection_string or not table_name:
            return False
        
        try:
            config = self.create_config(connection_string, table_name)
            conn = self.connect(config)
            
            # Create delete spec
            from ..base_datasource import Condition
            delete_spec = DeleteSpec(
                filters=Condition(field=pk_col, op='=', value=pk_value)
            )
            
            affected_rows = self.delete(conn, delete_spec)
            return affected_rows > 0
            
        except Exception as e:
            print(f"Error deleting row: {e}")
            return False

    @hookimpl
    def get_schema(self, table_config: dict):
        """Legacy method for backward compatibility"""
        connection_string = table_config.get('connection_string')
        table_name = table_config.get('table_name')
        
        if not connection_string or not table_name:
            return []
        
        try:
            config = self.create_config(connection_string, table_name)
            conn = self.connect(config)
            
            # Get table schema
            cur = conn.execute(f"PRAGMA table_info({table_name})")
            schema = []
            for row in cur.fetchall():
                schema.append({
                    'name': row[1],
                    'type': row[2],
                    'notnull': bool(row[3]),
                    'default': row[4],
                    'pk': bool(row[5])
                })
            return schema
            
        except Exception as e:
            print(f"Error getting schema: {e}")
            return []

    @hookimpl
    def test_connection(self, connection_config: dict):
        """Legacy method for backward compatibility"""
        try:
            connection_string = connection_config.get('connection_string', '')
            if not connection_string:
                return False
            
            # Try to create config and connect
            config = self.create_config(connection_string, 'test')
            conn = self.connect(config)
            conn.close()
            return True
            
        except Exception:
            return False 