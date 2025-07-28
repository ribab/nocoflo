"""
Integration tests for CRUD operations across all datasource plugins.
"""
import pytest
import pandas as pd
import tempfile
import os
import sqlite3
from unittest.mock import Mock, patch
from components.datasources.base_datasource import (
    QuerySpec, InsertSpec, UpdateSpec, DeleteSpec, 
    Condition, ConditionList, OrderItem
)
from components.datasources.plugins.sqlite_plugin import SQLiteConfig, SQLiteDataSource
from components.datasources.plugins.postgresql_plugin import PostgreSQLConfig, PostgreSQLDataSource
from components.datasources.plugins.mysql_plugin import MySQLConfig, MySQLDataSource


class TestCRUDOperationsIntegration:
    """Integration tests for CRUD operations across all plugins."""
    
    @pytest.fixture
    def temp_sqlite_db(self):
        """Create temporary SQLite database."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        # Create database with test table
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
    def sqlite_datasource(self):
        """Create SQLite datasource."""
        return SQLiteDataSource()
    
    @pytest.fixture
    def postgresql_datasource(self):
        """Create PostgreSQL datasource."""
        return PostgreSQLDataSource()
    
    @pytest.fixture
    def mysql_datasource(self):
        """Create MySQL datasource."""
        return MySQLDataSource()
    
    def test_sqlite_crud_operations(self, sqlite_datasource, temp_sqlite_db):
        """Test complete CRUD operations with SQLite."""
        config = SQLiteConfig(path=temp_sqlite_db, table_name="test_table")
        
        # Connect
        conn = sqlite_datasource.connect(config)
        # The connection wrapper already has _current_table set from config
        
        # Create - Insert data
        insert_data = InsertSpec(payload={
            "__table__": "test_table",
            "name": "Alice",
            "age": 25,
            "city": "New York"
        })
        result = sqlite_datasource.insert(conn, insert_data)
        assert result == 1
        
        # Read - Query data
        query = QuerySpec(limit=10, offset=0)
        df = sqlite_datasource.read(conn, query)
        assert len(df) == 1
        assert df.iloc[0]["name"] == "Alice"
        assert df.iloc[0]["age"] == 25
        
        # Update - Modify data
        update_spec = UpdateSpec(
            filters=Condition(field="name", op="=", value="Alice"),
            payload={"age": 26, "city": "Brooklyn"}
        )
        result = sqlite_datasource.update(conn, update_spec)
        assert result == 1
        
        # Read - Verify update
        df = sqlite_datasource.read(conn, query)
        assert df.iloc[0]["age"] == 26
        assert df.iloc[0]["city"] == "Brooklyn"
        
        # Delete - Remove data
        delete_spec = DeleteSpec(filters=Condition(field="name", op="=", value="Alice"))
        result = sqlite_datasource.delete(conn, delete_spec)
        assert result == 1
        
        # Read - Verify deletion
        df = sqlite_datasource.read(conn, query)
        assert len(df) == 0
        
        conn.close()
    
    @patch('sqlalchemy.create_engine')
    def test_postgresql_crud_operations(self, mock_create_engine, postgresql_datasource):
        """Test complete CRUD operations with PostgreSQL (mocked)."""
        # Mock connection setup
        mock_engine = Mock()
        mock_conn = Mock()
        mock_engine.connect.return_value = mock_conn
        mock_create_engine.return_value = mock_engine
        
        config = PostgreSQLConfig(
            user="test_user", password="test_pass", database="test_db", table_name="test_table"
        )
        
        # Connect
        conn = postgresql_datasource.connect(config)
        conn._current_table = "test_table"
        
        # Mock result for read operations
        mock_result = Mock()
        mock_result.fetchall.return_value = [
            (1, "Alice", 25, "New York"),
            (2, "Bob", 30, "Los Angeles")
        ]
        mock_result.keys.return_value = ["id", "name", "age", "city"]
        mock_conn.execute.return_value = mock_result
        
        # Create - Insert data
        insert_data = InsertSpec(payload={
            "__table__": "test_table",
            "name": "Alice",
            "age": 25,
            "city": "New York"
        })
        result = postgresql_datasource.insert(conn, insert_data)
        assert result == 1
        
        # Read - Query data
        query = QuerySpec(limit=10, offset=0)
        df = postgresql_datasource.read(conn, query)
        assert len(df) == 2
        assert "Alice" in df["name"].values
        
        # Update - Modify data
        update_spec = UpdateSpec(
            filters=Condition(field="name", op="=", value="Alice"),
            payload={"age": 26}
        )
        result = postgresql_datasource.update(conn, update_spec)
        assert result == 1
        
        # Delete - Remove data
        delete_spec = DeleteSpec(filters=Condition(field="name", op="=", value="Alice"))
        result = postgresql_datasource.delete(conn, delete_spec)
        assert result == 1
    
    @patch('sqlalchemy.create_engine')
    def test_mysql_crud_operations(self, mock_create_engine, mysql_datasource):
        """Test complete CRUD operations with MySQL (mocked)."""
        # Mock connection setup
        mock_engine = Mock()
        mock_conn = Mock()
        mock_engine.connect.return_value = mock_conn
        mock_create_engine.return_value = mock_engine
        
        config = MySQLConfig(
            user="test_user", password="test_pass", host="localhost", 
            port=3306, database="test_db", table_name="test_table"
        )
        
        # Connect
        conn = mysql_datasource.connect(config)
        conn._current_table = "test_table"
        
        # Mock result for read operations
        mock_result = Mock()
        mock_result.fetchall.return_value = [
            (1, "Alice", 25, "New York"),
            (2, "Bob", 30, "Los Angeles")
        ]
        mock_result.keys.return_value = ["id", "name", "age", "city"]
        mock_conn.execute.return_value = mock_result
        
        # Create - Insert data
        insert_data = InsertSpec(payload={
            "__table__": "test_table",
            "name": "Alice",
            "age": 25,
            "city": "New York"
        })
        result = mysql_datasource.insert(conn, insert_data)
        assert result == 1
        
        # Read - Query data
        query = QuerySpec(limit=10, offset=0)
        df = mysql_datasource.read(conn, query)
        assert len(df) == 2
        assert "Alice" in df["name"].values
        
        # Update - Modify data
        update_spec = UpdateSpec(
            filters=Condition(field="name", op="=", value="Alice"),
            payload={"age": 26}
        )
        result = mysql_datasource.update(conn, update_spec)
        assert result == 1
        
        # Delete - Remove data
        delete_spec = DeleteSpec(filters=Condition(field="name", op="=", value="Alice"))
        result = mysql_datasource.delete(conn, delete_spec)
        assert result == 1
    
    def test_complex_query_operations(self, sqlite_datasource, temp_sqlite_db):
        """Test complex query operations with SQLite."""
        config = SQLiteConfig(path=temp_sqlite_db, table_name="test_table")
        
        # Connect
        conn = sqlite_datasource.connect(config)
        # The connection wrapper already has _current_table set from config
        
        # Clear existing data and insert test data
        conn.execute("DELETE FROM test_table")
        conn.commit()
        
        # Insert test data
        test_data = [
            InsertSpec(payload={"__table__": "test_table", "name": "Alice", "age": 25, "city": "NYC"}),
            InsertSpec(payload={"__table__": "test_table", "name": "Bob", "age": 30, "city": "LA"}),
            InsertSpec(payload={"__table__": "test_table", "name": "Charlie", "age": 35, "city": "CHI"})
        ]
        
        for data in test_data:
            sqlite_datasource.insert(conn, data)
        
        # Test complex filter with AND
        complex_filter = ConditionList(
            mode="AND",
            filters=[
                Condition(field="age", op=">", value=25),
                Condition(field="city", op="in", value=["NYC", "LA"])
            ]
        )
        query = QuerySpec(limit=10, offset=0, filter=complex_filter)
        df = sqlite_datasource.read(conn, query)
        assert len(df) == 1  # Only Bob (age>25 and city=LA)
        
        # Test complex filter with OR
        complex_filter_or = ConditionList(
            mode="OR",
            filters=[
                Condition(field="age", op="<", value=30),
                Condition(field="city", op="=", value="CHI")
            ]
        )
        query = QuerySpec(limit=10, offset=0, filter=complex_filter_or)
        df = sqlite_datasource.read(conn, query)
        assert len(df) == 2  # Alice (age<30) and Charlie (city=CHI)
        
        conn.close()
    
    def test_bulk_operations(self, sqlite_datasource, temp_sqlite_db):
        """Test bulk operations with SQLite."""
        config = SQLiteConfig(path=temp_sqlite_db, table_name="test_table")
        
        # Connect
        conn = sqlite_datasource.connect(config)
        # The connection wrapper already has _current_table set from config
        
        # Clear existing data
        conn.execute("DELETE FROM test_table")
        conn.commit()
        
        # Bulk insert
        bulk_data = [
            InsertSpec(payload={"__table__": "test_table", "name": f"User{i}", "age": 20 + i, "city": f"City{i}"})
            for i in range(1, 6)
        ]
        
        for data in bulk_data:
            result = sqlite_datasource.insert(conn, data)
            assert result == 1
        
        # Verify bulk insert
        query = QuerySpec(limit=10, offset=0)
        df = sqlite_datasource.read(conn, query)
        assert len(df) == 5
        
        # Bulk update
        update_spec = UpdateSpec(
            filters=Condition(field="age", op="<", value=25),
            payload={"city": "Young City"}
        )
        result = sqlite_datasource.update(conn, update_spec)
        assert result == 2  # User1 and User2 have age < 25
        
        # Verify bulk update
        df = sqlite_datasource.read(conn, QuerySpec(limit=10, offset=0, filter=Condition(field="city", op="=", value="Young City")))
        assert len(df) == 2
        
        # Bulk delete
        delete_spec = DeleteSpec(filters=Condition(field="age", op=">", value=22))
        result = sqlite_datasource.delete(conn, delete_spec)
        assert result == 3  # User3, User4, User5 have age > 22
        
        # Verify bulk delete
        df = sqlite_datasource.read(conn, query)
        assert len(df) == 2  # Only User1 and User2 remain
        
        conn.close()
    
    def test_error_handling_integration(self, sqlite_datasource, temp_sqlite_db):
        """Test error handling in CRUD operations."""
        config = SQLiteConfig(path=temp_sqlite_db, table_name="test_table")
        
        # Connect
        conn = sqlite_datasource.connect(config)
        # The connection wrapper already has _current_table set from config
        
        # Test invalid insert (missing required field)
        # SQLite will allow this, so we test a different error case
        insert_data = InsertSpec(payload={"__table__": "test_table", "name": "Test"})  # Missing age
        result = sqlite_datasource.insert(conn, insert_data)
        assert result == 1  # SQLite allows NULL values
        
        # Test invalid update (non-existent record)
        update_spec = UpdateSpec(
            filters=Condition(field="name", op="=", value="NonExistent"),
            payload={"age": 30}
        )
        result = sqlite_datasource.update(conn, update_spec)
        assert result == 0  # No rows updated
        
        # Test invalid delete (non-existent record)
        delete_spec = DeleteSpec(filters=Condition(field="name", op="=", value="NonExistent"))
        result = sqlite_datasource.delete(conn, delete_spec)
        assert result == 0  # No rows deleted
        
        # Test valid operations after errors
        insert_data = InsertSpec(payload={"__table__": "test_table", "name": "Valid", "age": 25, "city": "Valid City"})
        result = sqlite_datasource.insert(conn, insert_data)
        assert result == 1
        
        # Verify valid insert
        query = QuerySpec(limit=10, offset=0)
        df = sqlite_datasource.read(conn, query)
        assert len(df) >= 2  # At least the two records we inserted
        
        conn.close() 