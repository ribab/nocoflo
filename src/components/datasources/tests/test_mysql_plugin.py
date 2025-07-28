"""
Tests for MySQL datasource plugin.
"""
import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.engine import Connection, Result
from ..plugins.mysql_plugin import MySQLDataSource, MySQLConfig
from ..base_datasource import (
    QuerySpec, InsertSpec, UpdateSpec, DeleteSpec,
    Condition, ConditionList, OrderItem
)


class TestMySQLDataSource:
    """Test MySQL datasource plugin."""
    
    @pytest.fixture
    def mysql_datasource(self):
        """Create MySQL datasource instance."""
        return MySQLDataSource()
    
    @pytest.fixture
    def mysql_config(self):
        """Create MySQL configuration."""
        return MySQLConfig(
            user="test_user",
            password="test_password",
            host="localhost",
            port=3306,
            database="test_db",
            table_name="test_table"
        )
    
    @pytest.fixture
    def mock_connection(self):
        """Create mock MySQL connection."""
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
    
    def test_mysql_datasource_name(self, mysql_datasource):
        """Test MySQL datasource name."""
        assert mysql_datasource.name == "mysql"
    
    def test_mysql_datasource_config_class(self, mysql_datasource):
        """Test MySQL datasource config class."""
        config_class = mysql_datasource.get_config_class()
        assert config_class == MySQLConfig
    
    @patch('sqlalchemy.create_engine')
    def test_mysql_connection(self, mock_create_engine, mysql_datasource, mysql_config):
        """Test MySQL connection establishment."""
        mock_engine = Mock()
        mock_conn = Mock()
        mock_engine.connect.return_value = mock_conn
        mock_create_engine.return_value = mock_engine
        
        conn = mysql_datasource.connect(mysql_config)
        
        # Verify engine was created with correct connection string
        expected_conn_string = "mysql+pymysql://test_user:test_password@localhost:3306/test_db"
        mock_create_engine.assert_called_once_with(expected_conn_string)
        mock_engine.connect.assert_called_once()
        assert conn == mock_conn
    
    def test_mysql_insert(self, mysql_datasource, mock_connection):
        """Test MySQL insert operation."""
        insert_data = InsertSpec(payload={
            "__table__": "test_table",
            "name": "Frank",
            "age": 27,
            "city": "Boston"
        })
        
        mock_result = Mock()
        mock_result.rowcount = 1
        mock_connection.execute.return_value = mock_result
        
        result = mysql_datasource.insert(mock_connection, insert_data)
        
        assert result == 1
        mock_connection.execute.assert_called_once()
        mock_connection.commit.assert_called_once()
        
        # Verify SQL was constructed correctly
        call_args = mock_connection.execute.call_args
        sql_text = call_args[0][0].text
        assert "INSERT INTO test_table" in sql_text
        assert "name, age, city" in sql_text
        assert ":name, :age, :city" in sql_text
    
    def test_mysql_insert_without_rowcount(self, mysql_datasource, mock_connection):
        """Test MySQL insert when result has no rowcount attribute."""
        insert_data = InsertSpec(payload={
            "__table__": "test_table",
            "name": "Frank",
            "age": 27
        })
        
        mock_result = Mock()
        # No rowcount attribute
        del mock_result.rowcount
        mock_connection.execute.return_value = mock_result
        
        result = mysql_datasource.insert(mock_connection, insert_data)
        
        assert result == 1  # Default return value
        mock_connection.commit.assert_called_once()
    
    def test_mysql_read_basic(self, mysql_datasource, mock_connection, mock_result):
        """Test MySQL basic read operation."""
        mock_connection.execute.return_value = mock_result
        
        query = QuerySpec(limit=10, offset=0)
        df = mysql_datasource.read(mock_connection, query)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
        assert list(df.columns) == ["id", "name", "age", "city"]
        
        # Verify SQL was constructed correctly
        call_args = mock_connection.execute.call_args
        sql_text = call_args[0][0].text
        assert "SELECT * FROM test_table" in sql_text
    
    def test_mysql_read_with_limit(self, mysql_datasource, mock_connection, mock_result):
        """Test MySQL read with limit."""
        mock_connection.execute.return_value = mock_result
        
        query = QuerySpec(limit=2, offset=0)
        df = mysql_datasource.read(mock_connection, query)
        
        assert len(df) == 3  # Mock returns 3 rows regardless
        
        # Verify LIMIT was added to SQL
        call_args = mock_connection.execute.call_args
        sql_text = call_args[0][0].text
        assert "LIMIT 2" in sql_text
    
    def test_mysql_read_with_offset(self, mysql_datasource, mock_connection, mock_result):
        """Test MySQL read with offset."""
        mock_connection.execute.return_value = mock_result
        
        query = QuerySpec(limit=10, offset=2)
        df = mysql_datasource.read(mock_connection, query)
        
        # Verify OFFSET was added to SQL
        call_args = mock_connection.execute.call_args
        sql_text = call_args[0][0].text
        assert "OFFSET 2" in sql_text
    
    def test_mysql_read_with_filter(self, mysql_datasource, mock_connection, mock_result):
        """Test MySQL read with filter."""
        mock_connection.execute.return_value = mock_result
        
        filter_condition = Condition(field="age", op=">", value=25)
        query = QuerySpec(limit=10, offset=0, filter=filter_condition)
        df = mysql_datasource.read(mock_connection, query)
        
        # Verify WHERE clause was added
        call_args = mock_connection.execute.call_args
        sql_text = call_args[0][0].text
        assert "WHERE" in sql_text
        assert "age >" in sql_text
    
    def test_mysql_read_with_in_filter(self, mysql_datasource, mock_connection, mock_result):
        """Test MySQL read with IN filter."""
        mock_connection.execute.return_value = mock_result
        
        filter_condition = Condition(field="city", op="in", value=["New York", "Chicago"])
        query = QuerySpec(limit=10, offset=0, filter=filter_condition)
        df = mysql_datasource.read(mock_connection, query)
        
        # Verify IN clause was added
        call_args = mock_connection.execute.call_args
        sql_text = call_args[0][0].text
        assert "WHERE" in sql_text
        assert "city IN" in sql_text
    
    def test_mysql_read_with_order_by(self, mysql_datasource, mock_connection, mock_result):
        """Test MySQL read with order by."""
        mock_connection.execute.return_value = mock_result
        
        order_items = [OrderItem(field="age", ascending=False)]
        query = QuerySpec(limit=10, offset=0, order_by=order_items)
        df = mysql_datasource.read(mock_connection, query)
        
        # Verify ORDER BY was added
        call_args = mock_connection.execute.call_args
        sql_text = call_args[0][0].text
        assert "ORDER BY" in sql_text
        assert "age DESC" in sql_text
    
    def test_mysql_read_empty_result(self, mysql_datasource, mock_connection):
        """Test MySQL read with no results."""
        mock_result = Mock()
        mock_result.fetchall.return_value = []
        mock_result.keys.return_value = ["id", "name", "age", "city"]
        mock_connection.execute.return_value = mock_result
        
        query = QuerySpec(limit=10, offset=0)
        df = mysql_datasource.read(mock_connection, query)
        
        assert len(df) == 0
        assert list(df.columns) == ["id", "name", "age", "city"]
    
    def test_mysql_update(self, mysql_datasource, mock_connection):
        """Test MySQL update operation."""
        filter_condition = Condition(field="id", op="=", value=1)
        update_spec = UpdateSpec(
            filters=filter_condition,
            payload={"age": 26, "city": "Brooklyn"}
        )
        
        mock_result = Mock()
        mock_result.rowcount = 1
        mock_connection.execute.return_value = mock_result
        
        result = mysql_datasource.update(mock_connection, update_spec)
        
        assert result == 1
        mock_connection.execute.assert_called_once()
        mock_connection.commit.assert_called_once()
        
        # Verify SQL was constructed correctly
        call_args = mock_connection.execute.call_args
        sql_text = call_args[0][0].text
        assert "UPDATE test_table" in sql_text
        assert "SET" in sql_text
        assert "WHERE" in sql_text
    
    def test_mysql_update_multiple_rows(self, mysql_datasource, mock_connection):
        """Test MySQL update affecting multiple rows."""
        filter_condition = Condition(field="age", op=">", value=30)
        update_spec = UpdateSpec(
            filters=filter_condition,
            payload={"city": "Updated City"}
        )
        
        mock_result = Mock()
        mock_result.rowcount = 2
        mock_connection.execute.return_value = mock_result
        
        result = mysql_datasource.update(mock_connection, update_spec)
        
        assert result == 2
        mock_connection.commit.assert_called_once()
    
    def test_mysql_delete(self, mysql_datasource, mock_connection):
        """Test MySQL delete operation."""
        filter_condition = Condition(field="id", op="=", value=1)
        delete_spec = DeleteSpec(filters=filter_condition)
        
        mock_result = Mock()
        mock_result.rowcount = 1
        mock_connection.execute.return_value = mock_result
        
        result = mysql_datasource.delete(mock_connection, delete_spec)
        
        assert result == 1
        mock_connection.execute.assert_called_once()
        mock_connection.commit.assert_called_once()
        
        # Verify SQL was constructed correctly
        call_args = mock_connection.execute.call_args
        sql_text = call_args[0][0].text
        assert "DELETE FROM test_table" in sql_text
        assert "WHERE" in sql_text
    
    def test_mysql_delete_multiple_rows(self, mysql_datasource, mock_connection):
        """Test MySQL delete affecting multiple rows."""
        filter_condition = Condition(field="age", op=">", value=30)
        delete_spec = DeleteSpec(filters=filter_condition)
        
        mock_result = Mock()
        mock_result.rowcount = 2
        mock_connection.execute.return_value = mock_result
        
        result = mysql_datasource.delete(mock_connection, delete_spec)
        
        assert result == 2
        mock_connection.commit.assert_called_once()
    
    def test_mysql_build_where_simple(self, mysql_datasource):
        """Test MySQL _build_where with simple condition."""
        condition = Condition(field="age", op=">", value=25)
        where_clause, params = mysql_datasource._build_where(condition, {})
        
        assert "age >" in where_clause
        assert ":p_0" in where_clause
        assert "p_0" in params
        assert params["p_0"] == 25
    
    def test_mysql_build_where_in_operator(self, mysql_datasource):
        """Test MySQL _build_where with IN operator."""
        condition = Condition(field="city", op="in", value=["New York", "Chicago"])
        where_clause, params = mysql_datasource._build_where(condition, {})
        
        assert "city IN" in where_clause
        assert ":p_0_0" in where_clause
        assert ":p_0_1" in where_clause
        assert "p_0_0" in params
        assert "p_0_1" in params
        assert params["p_0_0"] == "New York"
        assert params["p_0_1"] == "Chicago"
    
    def test_mysql_build_where_complex_and(self, mysql_datasource):
        """Test MySQL _build_where with complex AND condition."""
        conditions = [
            Condition(field="age", op=">", value=25),
            Condition(field="city", op="=", value="New York")
        ]
        condition_list = ConditionList(mode="AND", filters=conditions)
        where_clause, params = mysql_datasource._build_where(condition_list, {})
        
        assert "AND" in where_clause
        assert "age >" in where_clause
        assert "city =" in where_clause
        assert len(params) == 2
    
    def test_mysql_build_where_complex_or(self, mysql_datasource):
        """Test MySQL _build_where with complex OR condition."""
        conditions = [
            Condition(field="age", op=">", value=30),
            Condition(field="age", op="<", value=25)
        ]
        condition_list = ConditionList(mode="OR", filters=conditions)
        where_clause, params = mysql_datasource._build_where(condition_list, {})
        
        assert "OR" in where_clause
        assert "age >" in where_clause
        assert "age <" in where_clause
        assert len(params) == 2
    
    def test_mysql_build_where_nested_conditions(self, mysql_datasource):
        """Test MySQL _build_where with nested conditions."""
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
        
        where_clause, params = mysql_datasource._build_where(outer_list, {})
        
        assert "OR" in where_clause
        assert "AND" in where_clause
        assert "age >" in where_clause
        assert "city =" in where_clause
        assert "age <" in where_clause
        assert len(params) == 3


class TestMySQLDataSourceErrorHandling:
    """Test MySQL datasource error handling."""
    
    @pytest.fixture
    def mysql_datasource(self):
        """Create MySQL datasource instance."""
        return MySQLDataSource()
    
    @patch('sqlalchemy.create_engine')
    def test_mysql_connection_failure(self, mock_create_engine, mysql_datasource, mysql_config):
        """Test MySQL connection failure."""
        mock_create_engine.side_effect = Exception("Connection failed")
        
        with pytest.raises(Exception):
            mysql_datasource.connect(mysql_config)
    
    def test_mysql_insert_failure(self, mysql_datasource, mock_connection):
        """Test MySQL insert failure."""
        insert_data = InsertSpec(payload={
            "__table__": "test_table",
            "name": "Frank",
            "age": 27
        })
        
        mock_connection.execute.side_effect = Exception("Insert failed")
        
        with pytest.raises(Exception):
            mysql_datasource.insert(mock_connection, insert_data)
    
    def test_mysql_read_failure(self, mysql_datasource, mock_connection):
        """Test MySQL read failure."""
        query = QuerySpec(limit=10, offset=0)
        mock_connection.execute.side_effect = Exception("Read failed")
        
        with pytest.raises(Exception):
            mysql_datasource.read(mock_connection, query)
    
    def test_mysql_update_failure(self, mysql_datasource, mock_connection):
        """Test MySQL update failure."""
        filter_condition = Condition(field="id", op="=", value=1)
        update_spec = UpdateSpec(
            filters=filter_condition,
            payload={"age": 26}
        )
        
        mock_connection.execute.side_effect = Exception("Update failed")
        
        with pytest.raises(Exception):
            mysql_datasource.update(mock_connection, update_spec)
    
    def test_mysql_delete_failure(self, mysql_datasource, mock_connection):
        """Test MySQL delete failure."""
        filter_condition = Condition(field="id", op="=", value=1)
        delete_spec = DeleteSpec(filters=filter_condition)
        
        mock_connection.execute.side_effect = Exception("Delete failed")
        
        with pytest.raises(Exception):
            mysql_datasource.delete(mock_connection, delete_spec) 