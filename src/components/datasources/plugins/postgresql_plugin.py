from pluggy import HookimplMarker
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, Connection
from pydantic import Field
from ..base_datasource import (
    BaseDataSourceConfig, InsertSpec, QuerySpec, UpdateSpec, DeleteSpec, ConditionUnion, Condition
)

hookimpl = HookimplMarker("datasource")

class PostgreSQLConfig(BaseDataSourceConfig):
    """PostgreSQL configuration"""
    user: str = Field(..., description="Database username")
    password: str = Field(..., description="Database password")
    host: str = Field(default="localhost", description="Database host")
    port: int = Field(default=5432, description="Database port")
    database: str = Field(..., description="Database name")

class PostgreSQLDataSource:
    name = "postgresql"

    @classmethod
    def get_config_class(cls):
        return PostgreSQLConfig

    @hookimpl
    def connect(self, config: PostgreSQLConfig) -> Connection:
        """
        Connect to PostgreSQL using SQLAlchemy and the provided config.
        """
        if 'connection_string' in config:
            engine = create_engine(config['connection_string'])
        else:
            user = config.user
            password = config.password
            host = config.host
            port = config.port
            database = config.database
            engine = create_engine(
                f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"
            )
        conn = engine.connect()
        return conn

    @hookimpl
    def insert(self, conn: Connection, data: InsertSpec):
        table = data.payload.pop("__table__")
        keys = ", ".join(data.payload.keys())
        placeholders = ", ".join([f":{k}" for k in data.payload])
        sql = text(f"INSERT INTO {table} ({keys}) VALUES ({placeholders})")
        result = conn.execute(sql, data.payload)
        conn.commit()
        return result.rowcount if hasattr(result, "rowcount") else 1

    @hookimpl
    def read(self, conn: Connection, query: QuerySpec):
        table = getattr(conn, '_current_table', 'data')
        base_query = f"SELECT * FROM {table}"
        params = {}

        if query.filter:
            where_clause, where_params = self._build_where(query.filter, params)
            base_query += f" WHERE {where_clause}"

        if query.order_by:
            order_parts = [f"{o.field} {'ASC' if o.ascending else 'DESC'}" for o in query.order_by]
            base_query += " ORDER BY " + ", ".join(order_parts)

        if query.limit:
            base_query += f" LIMIT {query.limit}"

        if query.offset:
            base_query += f" OFFSET {query.offset}"

        sql = text(base_query)
        result = conn.execute(sql, params)
        rows = result.fetchall()
        columns = result.keys()
        if rows:
            return pd.DataFrame(rows, columns=columns)
        else:
            # Return empty DataFrame with correct columns
            return pd.DataFrame(columns=columns)

    def _build_where(self, node: ConditionUnion, params: dict, param_prefix="p") -> tuple[str, dict]:
        """
        Recursively build SQLAlchemy-compatible WHERE clause and params dict.
        """
        if isinstance(node, Condition):
            param_name = f"{param_prefix}_{len(params)}"
            if node.op == 'in':
                placeholders = []
                for idx, val in enumerate(node.value):
                    pname = f"{param_name}_{idx}"
                    placeholders.append(f":{pname}")
                    params[pname] = val
                clause = f"{node.field} IN ({', '.join(placeholders)})"
                return clause, params
            else:
                clause = f"{node.field} {node.op} :{param_name}"
                params[param_name] = node.value
                return clause, params
        else:
            clauses = []
            for idx, sub in enumerate(node.filters):
                sub_clause, params = self._build_where(sub, params, f"{param_prefix}{idx}")
                clauses.append(f"({sub_clause})")
            connector = " AND " if node.mode == 'AND' else " OR "
            return connector.join(clauses), params

    @hookimpl
    def update(self, conn: Connection, spec: UpdateSpec):
        table = getattr(conn, '_current_table', 'data')
        set_clause = ", ".join([f"{k}=:{k}" for k in spec.payload.keys()])
        where_clause, params = self._build_where(spec.filters, {})
        sql = text(f"UPDATE {table} SET {set_clause} WHERE {where_clause}")
        result = conn.execute(sql, {**spec.payload, **params})
        conn.commit()
        return result.rowcount if hasattr(result, "rowcount") else 0

    @hookimpl
    def delete(self, conn: Connection, spec: DeleteSpec):
        table = getattr(conn, '_current_table', 'data')
        where_clause, params = self._build_where(spec.filters, {})
        sql = text(f"DELETE FROM {table} WHERE {where_clause}")
        result = conn.execute(sql, params)
        conn.commit()
        return result.rowcount if hasattr(result, "rowcount") else 0 