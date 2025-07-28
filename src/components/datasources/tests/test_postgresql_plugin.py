"""
Tests for PostgreSQL datasource plugin.
"""
import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.engine import Connection, Result
from ..plugins.postgresql_plugin import PostgreSQLDataSource, PostgreSQLConfig
from ..base_datasource import (
    QuerySpec, InsertSpec, UpdateSpec, DeleteSpec,
    Condition, ConditionList, OrderItem
)


class TestPostgreSQLDataSource:
    """Test PostgreSQL datasource plugin."""
    
    @pytest.fixture
    def postgresql_datasource(self):
        """Create PostgreSQL datasource instance."""
        return PostgreSQLDataSource()
    
    @pytest.fixture
    def postgresql_config(self):
        """Create PostgreSQL configuration."""
        return PostgreSQLConfig(
            user="test_user",
            password="test_password",
            host="localhost",
            port=5432,
            database="test_db",
            table_name="test_table"
        )
    
    @pytest.fixture
    def mock_connection(self):
        """Create mock PostgreSQL connection."""
        mock_conn = Mock(spec=Connection)
        mock_conn._current_table = "test_table"
        mock_conn.commit = Mock()
        return mock_conn
    
    @pytest.fixture
    def mock_result(self):
        """Create mock result set."""
        mock_result = Mock(spec=Result)
        mock_result.fetchall.return_value = [
            (1, "Alice", 25, "New York"),
            (2, "Bob", 30, "Los Angeles"),
            (3, "Charlie", 35, "Chicago")
        ]
        mock_result.keys.return_value = ["id", "name", "age", "city"]
        return mock_result
    
    def test_postgresql_datasource_name(self, postgresql_datasource):
        """Test PostgreSQL datasource name."""
        assert postgresql_datasource.name == "postgresql"
    
    def test_postgresql_datasource_config_class(self, postgresql_datasource):
        """Test PostgreSQL datasource config class."""
        config_class = postgresql_datasource.get_config_class()
        assert config_class == PostgreSQLConfig
    
    @patch('sqlalchemy.create_engine')
    def test_postgresql_connection(self, mock_create_engine, postgresql_datasource, postgresql_config):
        """Test PostgreSQL connection establishment."""
        mock_engine = Mock()
        mock_conn = Mock()
        mock_engine.connect.return_value = mock_conn
        mock_create_engine.return_value = mock_engine
        
        conn = postgresql_datasource.connect(postgresql_config)
        
        # Verify engine was created with correct connection string
        expected_conn_string = "postgresql+psycopg2://test_user:test_password@localhost:5432/test_db"
        mock_create_engine.assert_called_once_with(expected_conn_string)
        mock_engine.connect.assert_called_once()
        assert conn == mock_conn
    
    @patch('sqlalchemy.create_engine')
    def test_postgresql_connection_with_connection_string(self, mock_create_engine, postgresql_datasource):
        """Test PostgreSQL connection with connection string."""
        config_dict = {
            'connection_string': 'postgresql://user:pass@host:5432/db',
            'table_name': 'test_table'
        }
        mock_engine = Mock()
        mock_conn = Mock()
        mock_engine.connect.return_value = mock_conn
        mock_create_engine.return_value = mock_engine
        
        conn = postgresql_datasource.connect(config_dict)
        
        mock_create_engine.assert_called_once_with('postgresql://user:pass@host:5432/db')
        assert conn == mock_conn
    
    def test_postgresql_insert(self, postgresql_datasource, mock_connection):
        """Test PostgreSQL insert operation."""
        insert_data = InsertSpec(payload={
            "__table__": "test_table",
            "name": "Frank",
            "age": 27,
            "city": "Boston"
        })
        
        mock_result = Mock()
        mock_result.rowcount = 1
        mock_connection.execute.return_value = mock_result
        
        result = postgresql_datasource.insert(mock_connection, insert_data)
        
        assert result == 1
        mock_connection.execute.assert_called_once()
        mock_connection.commit.assert_called_once()
        
        # Verify SQL was constructed correctly
        call_args = mock_connection.execute.call_args
        sql_text = call_args[0][0].text
        assert "INSERT INTO test_table" in sql_text
        assert "name, age, city" in sql_text
        assert ":name, :age, :city" in sql_text
    
    def test_postgresql_insert_without_rowcount(self, postgresql_datasource, mock_connection):
        """Test PostgreSQL insert when result has no rowcount attribute."""
        insert_data = InsertSpec(payload={
            "__table__": "test_table",
            "name": "Frank",
            "age": 27
        })
        
        mock_result = Mock()
        # No rowcount attribute
        del mock_result.rowcount
        mock_connection.execute.return_value = mock_result
        
        result = postgresql_datasource.insert(mock_connection, insert_data)
        
        assert result == 1  # Default return value
        mock_connection.commit.assert_called_once()
    
    def test_postgresql_read_basic(self, postgresql_datasource, mock_connection, mock_result):
        """Test PostgreSQL basic read operation."""
        mock_connection.execute.return_value = mock_result
        
        query = QuerySpec(limit=10, offset=0)
        df = postgresql_datasource.read(mock_connection, query)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
        assert list(df.columns) == ["id", "name", "age", "city"]
        
        # Verify SQL was constructed correctly
        call_args = mock_connection.execute.call_args
        sql_text = call_args[0][0].text
        assert "SELECT * FROM test_table" in sql_text
    
    def test_postgresql_read_with_limit(self, postgresql_datasource, mock_connection, mock_result):
        """Test PostgreSQL read with limit."""
        mock_connection.execute.return_value = mock_result
        
        query = QuerySpec(limit=2, offset=0)
        df = postgresql_datasource.read(mock_connection, query)
        
        assert len(df) == 3  # Mock returns 3 rows regardless
        
        # Verify LIMIT was added to SQL
        call_args = mock_connection.execute.call_args
        sql_text = call_args[0][0].text
        assert "LIMIT 2" in sql_text
    
    def test_postgresql_read_with_offset(self, postgresql_datasource, mock_connection, mock_result):
        """Test PostgreSQL read with offset."""
        mock_connection.execute.return_value = mock_result
        
        query = QuerySpec(limit=10, offset=2)
        df = postgresql_datasource.read(mock_connection, query)
        
        # Verify OFFSET was added to SQL
        call_args = mock_connection.execute.call_args
        sql_text = call_args[0][0].text
        assert "OFFSET 2" in sql_text
    
    def test_postgresql_read_with_filter(self, postgresql_datasource, mock_connection, mock_result):
        """Test PostgreSQL read with filter."""
        mock_connection.execute.return_value = mock_result
        
        filter_condition = Condition(field="age", op=">", value=25)
        query = QuerySpec(limit=10, offset=0, filter=filter_condition)
        df = postgresql_datasource.read(mock_connection, query)
        
        # Verify WHERE clause was added
        call_args = mock_connection.execute.call_args
        sql_text = call_args[0][0].text
        assert "WHERE" in sql_text
        assert "age >" in sql_text
    
    def test_postgresql_read_with_in_filter(self, postgresql_datasource, mock_connection, mock_result):
        """Test PostgreSQL read with IN filter."""
        mock_connection.execute.return_value = mock_result
        
        filter_condition = Condition(field="city", op="in", value=["New York", "Chicago"])
        query = QuerySpec(limit=10, offset=0, filter=filter_condition)
        df = postgresql_datasource.read(mock_connection, query)
        
        # Verify IN clause was added
        call_args = mock_connection.execute.call_args
        sql_text = call_args[0][0].text
        assert "WHERE" in sql_text
        assert "city IN" in sql_text
    
    def test_postgresql_read_with_order_by(self, postgresql_datasource, mock_connection, mock_result):
        """Test PostgreSQL read with order by."""
        mock_connection.execute.return_value = mock_result
        
        order_items = [OrderItem(field="age", ascending=False)]
        query = QuerySpec(limit=10, offset=0, order_by=order_items)
        df = postgresql_datasource.read(mock_connection, query)
        
        # Verify ORDER BY was added
        call_args = mock_connection.execute.call_args
        sql_text = call_args[0][0].text
        assert "ORDER BY" in sql_text
        assert "age DESC" in sql_text
    
    def test_postgresql_read_empty_result(self, postgresql_datasource, mock_connection):
        """Test PostgreSQL read with no results."""
        mock_result = Mock()
        mock_result.fetchall.return_value = []
        mock_result.keys.return_value = ["id", "name", "age", "city"]
        mock_connection.execute.return_value = mock_result
        
        query = QuerySpec(limit=10, offset=0)
        df = postgresql_datasource.read(mock_connection, query)
        
        assert len(df) == 0
        assert list(df.columns) == ["id", "name", "age", "city"]
    
    def test_postgresql_update(self, postgresql_datasource, mock_connection):
        """Test PostgreSQL update operation."""
        filter_condition = Condition(field="id", op="=", value=1)
        update_spec = UpdateSpec(
            filters=filter_condition,
            payload={"age": 26, "city": "Brooklyn"}
        )
        
        mock_result = Mock()
        mock_result.rowcount = 1
        mock_connection.execute.return_value = mock_result
        
        result = postgresql_datasource.update(mock_connection, update_spec)
        
        assert result == 1
        mock_connection.execute.assert_called_once()
        mock_connection.commit.assert_called_once()
        
        # Verify SQL was constructed correctly
        call_args = mock_connection.execute.call_args
        sql_text = call_args[0][0].text
        assert "UPDATE test_table" in sql_text
        assert "SET" in sql_text
        assert "WHERE" in sql_text
    
    def test_postgresql_update_multiple_rows(self, postgresql_datasource, mock_connection):
        """Test PostgreSQL update affecting multiple rows."""
        filter_condition = Condition(field="age", op=">", value=30)
        update_spec = UpdateSpec(
            filters=filter_condition,
            payload={"city": "Updated City"}
        )
        
        mock_result = Mock()
        mock_result.rowcount = 2
        mock_connection.execute.return_value = mock_result
        
        result = postgresql_datasource.update(mock_connection, update_spec)
        
        assert result == 2
        mock_connection.commit.assert_called_once()
    
    def test_postgresql_delete(self, postgresql_datasource, mock_connection):
        """Test PostgreSQL delete operation."""
        filter_condition = Condition(field="id", op="=", value=1)
        delete_spec = DeleteSpec(filters=filter_condition)
        
        mock_result = Mock()
        mock_result.rowcount = 1
        mock_connection.execute.return_value = mock_result
        
        result = postgresql_datasource.delete(mock_connection, delete_spec)
        
        assert result == 1
        mock_connection.execute.assert_called_once()
        mock_connection.commit.assert_called_once()
        
        # Verify SQL was constructed correctly
        call_args = mock_connection.execute.call_args
        sql_text = call_args[0][0].text
        assert "DELETE FROM test_table" in sql_text
        assert "WHERE" in sql_text
    
    def test_postgresql_delete_multiple_rows(self, postgresql_datasource, mock_connection):
        """Test PostgreSQL delete affecting multiple rows."""
        filter_condition = Condition(field="age", op=">", value=30)
        delete_spec = DeleteSpec(filters=filter_condition)
        
        mock_result = Mock()
        mock_result.rowcount = 2
        mock_connection.execute.return_value = mock_result
        
        result = postgresql_datasource.delete(mock_connection, delete_spec)
        
        assert result == 2
        mock_connection.commit.assert_called_once()
    
    def test_postgresql_build_where_simple(self, postgresql_datasource):
        """Test PostgreSQL _build_where with simple condition."""
        condition = Condition(field="age", op=">", value=25)
        where_clause, params = postgresql_datasource._build_where(condition, {})
        
        assert "age >" in where_clause
        assert ":p_0" in where_clause
        assert "p_0" in params
        assert params["p_0"] == 25
    
    def test_postgresql_build_where_in_operator(self, postgresql_datasource):
        """Test PostgreSQL _build_where with IN operator."""
        condition = Condition(field="city", op="in", value=["New York", "Chicago"])
        where_clause, params = postgresql_datasource._build_where(condition, {})
        
        assert "city IN" in where_clause
        assert ":p_0_0" in where_clause
        assert ":p_0_1" in where_clause
        assert "p_0_0" in params
        assert "p_0_1" in params
        assert params["p_0_0"] == "New York"
        assert params["p_0_1"] == "Chicago"
    
    def test_postgresql_build_where_complex_and(self, postgresql_datasource):
        """Test PostgreSQL _build_where with complex AND condition."""
        conditions = [
            Condition(field="age", op=">", value=25),
            Condition(field="city", op="=", value="New York")
        ]
        condition_list = ConditionList(mode="AND", filters=conditions)
        where_clause, params = postgresql_datasource._build_where(condition_list, {})
        
        assert "AND" in where_clause
        assert "age >" in where_clause
        assert "city =" in where_clause
        assert len(params) == 2
    
    def test_postgresql_build_where_complex_or(self, postgresql_datasource):
        """Test PostgreSQL _build_where with complex OR condition."""
        conditions = [
            Condition(field="age", op=">", value=30),
            Condition(field="age", op="<", value=25)
        ]
        condition_list = ConditionList(mode="OR", filters=conditions)
        where_clause, params = postgresql_datasource._build_where(condition_list, {})
        
        assert "OR" in where_clause
        assert "age >" in where_clause
        assert "age <" in where_clause
        assert len(params) == 2
    
    def test_postgresql_build_where_nested_conditions(self, postgresql_datasource):
        """Test PostgreSQL _build_where with nested conditions."""
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
        
        where_clause, params = postgresql_datasource._build_where(outer_list, {})
        
        assert "OR" in where_clause
        assert "AND" in where_clause
        assert "age >" in where_clause
        assert "city =" in where_clause
        assert "age <" in where_clause
        assert len(params) == 3


class TestPostgreSQLDataSourceErrorHandling:
    """Test PostgreSQL datasource error handling."""
    
    @pytest.fixture
    def postgresql_datasource(self):
        """Create PostgreSQL datasource instance."""
        return PostgreSQLDataSource()
    
    @patch('sqlalchemy.create_engine')
    def test_postgresql_connection_failure(self, mock_create_engine, postgresql_datasource, postgresql_config):
        """Test PostgreSQL connection failure."""
        mock_create_engine.side_effect = Exception("Connection failed")
        
        with pytest.raises(Exception):
            postgresql_datasource.connect(postgresql_config)
    
    def test_postgresql_insert_failure(self, postgresql_datasource, mock_connection):
        """Test PostgreSQL insert failure."""
        insert_data = InsertSpec(payload={
            "__table__": "test_table",
            "name": "Frank",
            "age": 27
        })
        
        mock_connection.execute.side_effect = Exception("Insert failed")
        
        with pytest.raises(Exception):
            postgresql_datasource.insert(mock_connection, insert_data)
    
    def test_postgresql_read_failure(self, postgresql_datasource, mock_connection):
        """Test PostgreSQL read failure."""
        query = QuerySpec(limit=10, offset=0)
        mock_connection.execute.side_effect = Exception("Read failed")
        
        with pytest.raises(Exception):
            postgresql_datasource.read(mock_connection, query)
    
    def test_postgresql_update_failure(self, postgresql_datasource, mock_connection):
        """Test PostgreSQL update failure."""
        filter_condition = Condition(field="id", op="=", value=1)
        update_spec = UpdateSpec(
            filters=filter_condition,
            payload={"age": 26}
        )
        
        mock_connection.execute.side_effect = Exception("Update failed")
        
        with pytest.raises(Exception):
            postgresql_datasource.update(mock_connection, update_spec)
    
    def test_postgresql_delete_failure(self, postgresql_datasource, mock_connection):
        """Test PostgreSQL delete failure."""
        filter_condition = Condition(field="id", op="=", value=1)
        delete_spec = DeleteSpec(filters=filter_condition)
        
        mock_connection.execute.side_effect = Exception("Delete failed")
        
        with pytest.raises(Exception):
            postgresql_datasource.delete(mock_connection, delete_spec) 