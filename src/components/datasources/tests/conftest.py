"""
Common fixtures for datasource plugin tests.
"""
import pytest
import tempfile
import os
import sqlite3
import pandas as pd
from typing import Dict, Any
from unittest.mock import Mock, MagicMock

from ..base_datasource import (
    QuerySpec, InsertSpec, UpdateSpec, DeleteSpec,
    Condition, ConditionList, OrderItem
)
from ..plugins.sqlite_plugin import SQLiteDataSource
from ..plugins.postgresql_plugin import PostgreSQLDataSource
from ..plugins.mysql_plugin import MySQLDataSource


@pytest.fixture
def sample_data():
    """Sample data for testing CRUD operations."""
    return [
        {"id": 1, "name": "Alice", "age": 25, "city": "New York"},
        {"id": 2, "name": "Bob", "age": 30, "city": "Los Angeles"},
        {"id": 3, "name": "Charlie", "age": 35, "city": "Chicago"},
        {"id": 4, "name": "Diana", "age": 28, "city": "Houston"},
        {"id": 5, "name": "Eve", "age": 32, "city": "Phoenix"}
    ]


@pytest.fixture
def sample_df(sample_data):
    """Sample DataFrame for testing."""
    return pd.DataFrame(sample_data)


@pytest.fixture
def temp_sqlite_db():
    """Create a temporary SQLite database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    # Create database with sample table
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE test_table (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            age INTEGER,
            city TEXT
        )
    """)
    
    # Insert sample data
    sample_data = [
        (1, "Alice", 25, "New York"),
        (2, "Bob", 30, "Los Angeles"),
        (3, "Charlie", 35, "Chicago"),
        (4, "Diana", 28, "Houston"),
        (5, "Eve", 32, "Phoenix")
    ]
    conn.executemany(
        "INSERT INTO test_table (id, name, age, city) VALUES (?, ?, ?, ?)",
        sample_data
    )
    conn.commit()
    conn.close()
    
    yield db_path
    
    # Cleanup
    os.unlink(db_path)


@pytest.fixture
def sqlite_config(temp_sqlite_db):
    """SQLite configuration for testing."""
    from components.datasources.plugins.sqlite_plugin import SQLiteConfig
    return SQLiteConfig(path=temp_sqlite_db, table_name="test_table")


@pytest.fixture
def postgresql_config():
    """PostgreSQL configuration for testing."""
    return {
        "user": "test_user",
        "password": "test_password",
        "host": "localhost",
        "port": 5432,
        "database": "test_db",
        "table_name": "test_table"
    }


@pytest.fixture
def mysql_config():
    """MySQL configuration for testing."""
    return {
        "user": "test_user",
        "password": "test_password",
        "host": "localhost",
        "port": 3306,
        "database": "test_db",
        "table_name": "test_table"
    }


@pytest.fixture
def sqlite_datasource():
    """SQLite datasource instance for testing."""
    return SQLiteDataSource()


@pytest.fixture
def postgresql_datasource():
    """PostgreSQL datasource instance for testing."""
    return PostgreSQLDataSource()


@pytest.fixture
def mysql_datasource():
    """MySQL datasource instance for testing."""
    return MySQLDataSource()


@pytest.fixture
def plugin_manager():
    """Plugin manager instance for testing."""
    from pluggy import PluginManager
    import importlib
    pm = PluginManager("datasource")
    pm.add_hookspecs(importlib.import_module("components.datasources.base_datasource"))
    return pm


@pytest.fixture
def mock_connection():
    """Mock database connection for testing."""
    mock_conn = Mock()
    mock_conn._current_table = "test_table"
    return mock_conn


@pytest.fixture
def basic_query_spec():
    """Basic query specification for testing."""
    return QuerySpec(limit=10, offset=0)


@pytest.fixture
def filtered_query_spec():
    """Query specification with filter for testing."""
    filter_condition = Condition(field="age", op=">", value=25)
    return QuerySpec(limit=10, offset=0, filter=filter_condition)


@pytest.fixture
def complex_filter_query_spec():
    """Query specification with complex filter for testing."""
    conditions = [
        Condition(field="age", op=">", value=25),
        Condition(field="city", op="in", value=["New York", "Chicago"])
    ]
    complex_filter = ConditionList(mode="AND", filters=conditions)
    return QuerySpec(limit=10, offset=0, filter=complex_filter)


@pytest.fixture
def ordered_query_spec():
    """Query specification with ordering for testing."""
    order_items = [
        OrderItem(field="age", ascending=False),
        OrderItem(field="name", ascending=True)
    ]
    return QuerySpec(limit=10, offset=0, order_by=order_items)


@pytest.fixture
def insert_spec():
    """Insert specification for testing."""
    payload = {
        "__table__": "test_table",
        "name": "Test User",
        "age": 30,
        "city": "Test City"
    }
    return InsertSpec(payload=payload)


@pytest.fixture
def update_spec():
    """Update specification for testing."""
    filter_condition = Condition(field="name", op="=", value="Test User")
    payload = {"age": 31, "city": "Updated City"}
    return UpdateSpec(filters=filter_condition, payload=payload)


@pytest.fixture
def delete_spec():
    """Delete specification for testing."""
    filter_condition = Condition(field="name", op="=", value="Test User")
    return DeleteSpec(filters=filter_condition)


@pytest.fixture
def mock_result_set():
    """Mock result set for testing."""
    mock_result = Mock()
    mock_result.fetchall.return_value = [
        (1, "Alice", 25, "New York"),
        (2, "Bob", 30, "Los Angeles"),
        (3, "Charlie", 35, "Chicago")
    ]
    mock_result.keys.return_value = ["id", "name", "age", "city"]
    return mock_result 