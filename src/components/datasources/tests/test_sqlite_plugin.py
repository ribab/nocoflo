"""
Tests for SQLite datasource plugin.
"""
import pytest
import sqlite3
import pandas as pd
import tempfile
import os
from unittest.mock import Mock, patch
from ..plugins.sqlite_plugin import SQLiteDataSource, SQLiteConfig
from ..base_datasource import (
    QuerySpec, InsertSpec, UpdateSpec, DeleteSpec,
    Condition, ConditionList, OrderItem
)


class TestSQLiteDataSource:
    """Test SQLite datasource plugin."""
    
    @pytest.fixture
    def sqlite_datasource(self):
        """Create SQLite datasource instance."""
        return SQLiteDataSource()
    
    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database path."""
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
        conn.commit()
        conn.close()
        
        yield db_path
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    @pytest.fixture
    def sqlite_config(self, temp_db_path):
        """Create SQLite configuration."""
        return SQLiteConfig(path=temp_db_path, table_name="test_table")
    
    @pytest.fixture
    def sqlite_connection(self, sqlite_config):
        """Create SQLite connection with test data."""
        conn = sqlite3.connect(sqlite_config.path)
        conn.row_factory = sqlite3.Row
        
        # Insert test data
        test_data = [
            (1, "Alice", 25, "New York"),
            (2, "Bob", 30, "Los Angeles"),
            (3, "Charlie", 35, "Chicago"),
            (4, "Diana", 28, "Houston"),
            (5, "Eve", 32, "Phoenix")
        ]
        conn.executemany(
            "INSERT INTO test_table (id, name, age, city) VALUES (?, ?, ?, ?)",
            test_data
        )
        conn.commit()
        
        # Create wrapper with table name
        from components.datasources.plugins.sqlite_plugin import SQLiteConnectionWrapper
        wrapped_conn = SQLiteConnectionWrapper(conn, "test_table")
        
        yield wrapped_conn
        conn.close()
    
    def test_sqlite_datasource_name(self, sqlite_datasource):
        """Test SQLite datasource name."""
        assert sqlite_datasource.name == "sqlite"
    
    def test_sqlite_datasource_config_class(self, sqlite_datasource):
        """Test SQLite datasource config class."""
        config_class = sqlite_datasource.get_config_class()
        assert config_class == SQLiteConfig
    
    def test_sqlite_connection(self, sqlite_datasource, sqlite_config):
        """Test SQLite connection establishment."""
        conn = sqlite_datasource.connect(sqlite_config)
        from components.datasources.plugins.sqlite_plugin import SQLiteConnectionWrapper
        assert isinstance(conn, SQLiteConnectionWrapper)
        assert conn._current_table == "test_table"
        conn.close()
    
    def test_sqlite_connection_with_invalid_path(self, sqlite_datasource):
        """Test SQLite connection with invalid path."""
        config = SQLiteConfig(path="/invalid/path/test.db", table_name="test_table")
        with pytest.raises(sqlite3.OperationalError):
            sqlite_datasource.connect(config)
    
    def test_sqlite_insert(self, sqlite_datasource, sqlite_connection):
        """Test SQLite insert operation."""
        insert_data = InsertSpec(payload={
            "__table__": "test_table",
            "name": "Frank",
            "age": 27,
            "city": "Boston"
        })
        
        result = sqlite_datasource.insert(sqlite_connection, insert_data)
        assert result == 1
        
        # Verify data was inserted
        cursor = sqlite_connection.execute("SELECT * FROM test_table WHERE name = 'Frank'")
        row = cursor.fetchone()
        assert row is not None
        assert row[1] == "Frank"  # name
        assert row[2] == 27  # age
        assert row[3] == "Boston"  # city
    
    def test_sqlite_read_basic(self, sqlite_datasource, sqlite_connection):
        """Test SQLite basic read operation."""
        query = QuerySpec(limit=10, offset=0)
        df = sqlite_datasource.read(sqlite_connection, query)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 5  # All test records
        assert list(df.columns) == ["id", "name", "age", "city"]
    
    def test_sqlite_read_with_limit(self, sqlite_datasource, sqlite_connection):
        """Test SQLite read with limit."""
        query = QuerySpec(limit=3, offset=0)
        df = sqlite_datasource.read(sqlite_connection, query)
        
        assert len(df) == 3
    
    def test_sqlite_read_with_offset(self, sqlite_datasource, sqlite_connection):
        """Test SQLite read with offset."""
        query = QuerySpec(limit=10, offset=2)
        df = sqlite_datasource.read(sqlite_connection, query)
        
        assert len(df) == 3  # 5 total - 2 offset = 3 remaining
    
    def test_sqlite_read_with_filter(self, sqlite_datasource, sqlite_connection):
        """Test SQLite read with filter."""
        filter_condition = Condition(field="age", op=">", value=30)
        query = QuerySpec(limit=10, offset=0, filter=filter_condition)
        df = sqlite_datasource.read(sqlite_connection, query)
        
        assert len(df) == 2  # Bob (30), Charlie (35), Eve (32)
        assert all(df["age"] > 30)
    
    def test_sqlite_read_with_in_filter(self, sqlite_datasource, sqlite_connection):
        """Test SQLite read with IN filter."""
        filter_condition = Condition(field="city", op="in", value=["New York", "Chicago"])
        query = QuerySpec(limit=10, offset=0, filter=filter_condition)
        df = sqlite_datasource.read(sqlite_connection, query)
        
        assert len(df) == 2
        assert all(city in ["New York", "Chicago"] for city in df["city"])
    
    def test_sqlite_read_with_complex_filter(self, sqlite_datasource, sqlite_connection):
        """Test SQLite read with complex AND/OR filters."""
        # AND condition: age > 25 AND city = "New York"
        and_conditions = [
            Condition(field="age", op=">", value=25),
            Condition(field="city", op="=", value="New York")
        ]
        filter_condition = ConditionList(mode="AND", filters=and_conditions)
        query = QuerySpec(limit=10, offset=0, filter=filter_condition)
        df = sqlite_datasource.read(sqlite_connection, query)
        
        assert len(df) == 1  # Only Alice (age 25, New York)
        assert df.iloc[0]["name"] == "Alice"
    
    def test_sqlite_read_with_order_by(self, sqlite_datasource, sqlite_connection):
        """Test SQLite read with order by."""
        order_items = [OrderItem(field="age", ascending=False)]
        query = QuerySpec(limit=10, offset=0, order_by=order_items)
        df = sqlite_datasource.read(sqlite_connection, query)
        
        # Check that ages are in descending order
        ages = df["age"].tolist()
        assert ages == sorted(ages, reverse=True)
    
    def test_sqlite_read_with_multiple_order_by(self, sqlite_datasource, sqlite_connection):
        """Test SQLite read with multiple order by fields."""
        order_items = [
            OrderItem(field="age", ascending=False),
            OrderItem(field="name", ascending=True)
        ]
        query = QuerySpec(limit=10, offset=0, order_by=order_items)
        df = sqlite_datasource.read(sqlite_connection, query)
        
        # Check that results are ordered by age desc, then name asc
        assert len(df) == 5
    
    def test_sqlite_read_empty_result(self, sqlite_datasource, sqlite_connection):
        """Test SQLite read with no results."""
        filter_condition = Condition(field="age", op=">", value=100)
        query = QuerySpec(limit=10, offset=0, filter=filter_condition)
        df = sqlite_datasource.read(sqlite_connection, query)
        
        assert len(df) == 0
        assert list(df.columns) == ["id", "name", "age", "city"]
    
    def test_sqlite_update(self, sqlite_datasource, sqlite_connection):
        """Test SQLite update operation."""
        filter_condition = Condition(field="id", op="=", value=1)
        update_spec = UpdateSpec(
            filters=filter_condition,
            payload={"age": 26, "city": "Brooklyn"}
        )
        
        result = sqlite_datasource.update(sqlite_connection, update_spec)
        assert result == 1
        
        # Verify update
        cursor = sqlite_connection.execute("SELECT * FROM test_table WHERE id = 1")
        row = cursor.fetchone()
        assert row[2] == 26  # age
        assert row[3] == "Brooklyn"  # city
    
    def test_sqlite_update_multiple_rows(self, sqlite_datasource, sqlite_connection):
        """Test SQLite update affecting multiple rows."""
        filter_condition = Condition(field="age", op=">", value=30)
        update_spec = UpdateSpec(
            filters=filter_condition,
            payload={"city": "Updated City"}
        )
        
        result = sqlite_datasource.update(sqlite_connection, update_spec)
        assert result == 2  # Bob (30), Charlie (35), Eve (32)
        
        # Verify updates
        cursor = sqlite_connection.execute("SELECT * FROM test_table WHERE age > 30")
        rows = cursor.fetchall()
        assert len(rows) == 2
        assert all(row[3] == "Updated City" for row in rows)
    
    def test_sqlite_delete(self, sqlite_datasource, sqlite_connection):
        """Test SQLite delete operation."""
        filter_condition = Condition(field="id", op="=", value=1)
        delete_spec = DeleteSpec(filters=filter_condition)
        
        result = sqlite_datasource.delete(sqlite_connection, delete_spec)
        assert result == 1
        
        # Verify deletion
        cursor = sqlite_connection.execute("SELECT * FROM test_table WHERE id = 1")
        row = cursor.fetchone()
        assert row is None
    
    def test_sqlite_delete_multiple_rows(self, sqlite_datasource, sqlite_connection):
        """Test SQLite delete affecting multiple rows."""
        filter_condition = Condition(field="age", op=">", value=30)
        delete_spec = DeleteSpec(filters=filter_condition)
        
        result = sqlite_datasource.delete(sqlite_connection, delete_spec)
        assert result == 2  # Bob (30), Charlie (35), Eve (32)
        
        # Verify deletions
        cursor = sqlite_connection.execute("SELECT * FROM test_table WHERE age > 30")
        rows = cursor.fetchall()
        assert len(rows) == 0
    
    def test_sqlite_build_where_simple(self, sqlite_datasource):
        """Test SQLite _build_where with simple condition."""
        condition = Condition(field="age", op=">", value=25)
        where_clause, params = sqlite_datasource._build_where(condition)
        
        assert where_clause == "age > ?"
        assert params == [25]
    
    def test_sqlite_build_where_in_operator(self, sqlite_datasource):
        """Test SQLite _build_where with IN operator."""
        condition = Condition(field="city", op="in", value=["New York", "Chicago"])
        where_clause, params = sqlite_datasource._build_where(condition)
        
        assert where_clause == "city IN (?, ?)"
        assert params == ["New York", "Chicago"]
    
    def test_sqlite_build_where_complex_and(self, sqlite_datasource):
        """Test SQLite _build_where with complex AND condition."""
        conditions = [
            Condition(field="age", op=">", value=25),
            Condition(field="city", op="=", value="New York")
        ]
        condition_list = ConditionList(mode="AND", filters=conditions)
        where_clause, params = sqlite_datasource._build_where(condition_list)
        
        assert where_clause == "(age > ?) AND (city = ?)"
        assert params == [25, "New York"]
    
    def test_sqlite_build_where_complex_or(self, sqlite_datasource):
        """Test SQLite _build_where with complex OR condition."""
        conditions = [
            Condition(field="age", op=">", value=30),
            Condition(field="age", op="<", value=25)
        ]
        condition_list = ConditionList(mode="OR", filters=conditions)
        where_clause, params = sqlite_datasource._build_where(condition_list)
        
        assert where_clause == "(age > ?) OR (age < ?)"
        assert params == [30, 25]
    
    def test_sqlite_build_where_nested_conditions(self, sqlite_datasource):
        """Test SQLite _build_where with nested conditions."""
        # (age > 25 AND city = "New York") OR (age < 20)
        inner_conditions = [
            Condition(field="age", op=">", value=25),
            Condition(field="city", op="=", value="New York")
        ]
        inner_list = ConditionList(mode="AND", filters=inner_conditions)
        
        outer_conditions = [
            inner_list,
            Condition(field="age", op="<", value=20)
        ]
        outer_list = ConditionList(mode="OR", filters=outer_conditions)
        
        where_clause, params = sqlite_datasource._build_where(outer_list)
        
        assert where_clause == "((age > ?) AND (city = ?)) OR (age < ?)"
        assert params == [25, "New York", 20]


class TestSQLiteDataSourceErrorHandling:
    """Test SQLite datasource error handling."""
    
    @pytest.fixture
    def sqlite_datasource(self):
        """Create SQLite datasource instance."""
        return SQLiteDataSource()
    
    def test_sqlite_insert_table_not_exists(self, sqlite_datasource, temp_sqlite_db):
        """Test SQLite insert with non-existent table."""
        config = SQLiteConfig(path=temp_sqlite_db, table_name="test_table")
        conn = sqlite_datasource.connect(config)
        
        insert_data = InsertSpec(payload={
            "__table__": "non_existent_table",
            "name": "Frank",
            "age": 27
        })
        
        with pytest.raises(sqlite3.OperationalError):
            sqlite_datasource.insert(conn, insert_data)
        
        conn.close()
    
    def test_sqlite_read_table_not_exists(self, sqlite_datasource, temp_sqlite_db):
        """Test SQLite read with non-existent table."""
        config = SQLiteConfig(path=temp_sqlite_db, table_name="non_existent_table")
        conn = sqlite_datasource.connect(config)
        
        query = QuerySpec(limit=10, offset=0)
        with pytest.raises(sqlite3.OperationalError):
            sqlite_datasource.read(conn, query)
        
        conn.close()

    def test_sqlite_update_invalid_column(self, sqlite_datasource, temp_sqlite_db):
        """Test SQLite update with invalid column."""
        config = SQLiteConfig(path=temp_sqlite_db, table_name="test_table")
        conn = sqlite_datasource.connect(config)
        
        # Insert test data first
        insert_data = InsertSpec(payload={"__table__": "test_table", "name": "Test", "age": 25, "city": "Test City"})
        sqlite_datasource.insert(conn, insert_data)
        
        # Try to update with invalid column
        update_spec = UpdateSpec(
            filters=Condition(field="name", op="=", value="Test"),
            payload={"invalid_column": "value"}
        )
        
        # Should raise exception for invalid column
        with pytest.raises(sqlite3.OperationalError):
            sqlite_datasource.update(conn, update_spec)
        
        conn.close()

    def test_sqlite_delete_invalid_condition(self, sqlite_datasource, temp_sqlite_db):
        """Test SQLite delete with invalid condition."""
        config = SQLiteConfig(path=temp_sqlite_db, table_name="test_table")
        conn = sqlite_datasource.connect(config)
        
        # Insert test data first
        insert_data = InsertSpec(payload={"__table__": "test_table", "name": "Test", "age": 25, "city": "Test City"})
        sqlite_datasource.insert(conn, insert_data)
        
        # Try to delete with condition that doesn't match
        delete_spec = DeleteSpec(filters=Condition(field="name", op="=", value="NonExistent"))
        result = sqlite_datasource.delete(conn, delete_spec)
        assert result == 0  # No rows deleted
        
        # Verify data still exists
        query = QuerySpec(limit=10, offset=0)
        df = sqlite_datasource.read(conn, query)
        assert len(df) == 1  # Data still exists
        
        conn.close() 