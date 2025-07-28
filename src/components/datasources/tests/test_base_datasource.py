"""
Tests for base datasource classes and configurations.
"""
import pytest
from pydantic import ValidationError
from ..base_datasource import (
    BaseDataSourceConfig, Condition, ConditionList, OrderItem, 
    QuerySpec, InsertSpec, UpdateSpec, DeleteSpec
)
from ..plugins.sqlite_plugin import SQLiteConfig
from ..plugins.postgresql_plugin import PostgreSQLConfig
from ..plugins.mysql_plugin import MySQLConfig


class TestBaseDataSourceConfig:
    """Test the base configuration class."""
    
    def test_base_config_validation(self):
        """Test that base config requires table_name."""
        # Valid config
        config = BaseDataSourceConfig(table_name="test_table")
        assert config.table_name == "test_table"
        
        # Invalid config - missing table_name
        with pytest.raises(ValidationError):
            BaseDataSourceConfig()
    
    def test_base_config_inheritance(self):
        """Test that specific configs inherit from base config."""
        # SQLite config
        sqlite_config = SQLiteConfig(path="/tmp/test.db", table_name="test_table")
        assert isinstance(sqlite_config, BaseDataSourceConfig)
        assert sqlite_config.table_name == "test_table"
        assert sqlite_config.path == "/tmp/test.db"
        
        # PostgreSQL config
        pg_config = PostgreSQLConfig(
            user="test_user", password="test_pass", database="test_db", table_name="test_table"
        )
        assert isinstance(pg_config, BaseDataSourceConfig)
        assert pg_config.table_name == "test_table"
        assert pg_config.user == "test_user"
        assert pg_config.host == "localhost"  # default value
        assert pg_config.port == 5432  # default value
        
        # MySQL config
        mysql_config = MySQLConfig(
            user="test_user", password="test_pass", host="localhost", 
            port=3306, database="test_db", table_name="test_table"
        )
        assert isinstance(mysql_config, BaseDataSourceConfig)
        assert mysql_config.table_name == "test_table"
        assert mysql_config.user == "test_user"


class TestSQLiteConfig:
    """Test SQLite configuration validation."""
    
    def test_valid_sqlite_config(self):
        """Test valid SQLite configuration."""
        config = SQLiteConfig(path="/tmp/test.db", table_name="test_table")
        assert config.path == "/tmp/test.db"
        assert config.table_name == "test_table"
    
    def test_sqlite_config_missing_path(self):
        """Test SQLite config validation with missing path."""
        with pytest.raises(ValidationError):
            SQLiteConfig(table_name="test_table")
    
    def test_sqlite_config_missing_table_name(self):
        """Test SQLite config validation with missing table_name."""
        with pytest.raises(ValidationError):
            SQLiteConfig(path="/tmp/test.db")


class TestPostgreSQLConfig:
    """Test PostgreSQL configuration validation."""
    
    def test_valid_postgresql_config(self):
        """Test valid PostgreSQL configuration."""
        config = PostgreSQLConfig(
            user="test_user", password="test_pass", database="test_db", table_name="test_table"
        )
        assert config.user == "test_user"
        assert config.password == "test_pass"
        assert config.database == "test_db"
        assert config.table_name == "test_table"
        assert config.host == "localhost"  # default
        assert config.port == 5432  # default
    
    def test_postgresql_config_with_custom_host_port(self):
        """Test PostgreSQL config with custom host and port."""
        config = PostgreSQLConfig(
            user="test_user", password="test_pass", host="custom.host", 
            port=5433, database="test_db", table_name="test_table"
        )
        assert config.host == "custom.host"
        assert config.port == 5433
    
    def test_postgresql_config_missing_required_fields(self):
        """Test PostgreSQL config validation with missing required fields."""
        # Missing user
        with pytest.raises(ValidationError):
            PostgreSQLConfig(password="test_pass", database="test_db", table_name="test_table")
        
        # Missing password
        with pytest.raises(ValidationError):
            PostgreSQLConfig(user="test_user", database="test_db", table_name="test_table")
        
        # Missing database
        with pytest.raises(ValidationError):
            PostgreSQLConfig(user="test_user", password="test_pass", table_name="test_table")


class TestMySQLConfig:
    """Test MySQL configuration validation."""
    
    def test_valid_mysql_config(self):
        """Test valid MySQL configuration."""
        config = MySQLConfig(
            user="test_user", password="test_pass", host="localhost", 
            port=3306, database="test_db", table_name="test_table"
        )
        assert config.user == "test_user"
        assert config.password == "test_pass"
        assert config.host == "localhost"
        assert config.port == 3306
        assert config.database == "test_db"
        assert config.table_name == "test_table"
    
    def test_mysql_config_missing_required_fields(self):
        """Test MySQL config validation with missing required fields."""
        # Missing user
        with pytest.raises(ValidationError):
            MySQLConfig(password="test_pass", host="localhost", port=3306, 
                       database="test_db", table_name="test_table")
        
        # Missing password
        with pytest.raises(ValidationError):
            MySQLConfig(user="test_user", host="localhost", port=3306, 
                       database="test_db", table_name="test_table")
        
        # Missing host
        with pytest.raises(ValidationError):
            MySQLConfig(user="test_user", password="test_pass", port=3306, 
                       database="test_db", table_name="test_table")


class TestCondition:
    """Test Condition model validation."""
    
    def test_valid_condition(self):
        """Test valid condition creation."""
        condition = Condition(field="age", op=">", value=25)
        assert condition.field == "age"
        assert condition.op == ">"
        assert condition.value == 25
    
    def test_condition_with_in_operator(self):
        """Test condition with 'in' operator."""
        condition = Condition(field="city", op="in", value=["New York", "Los Angeles"])
        assert condition.field == "city"
        assert condition.op == "in"
        assert condition.value == ["New York", "Los Angeles"]
    
    def test_condition_invalid_operator(self):
        """Test condition with invalid operator."""
        with pytest.raises(ValidationError):
            Condition(field="age", op="invalid", value=25)


class TestConditionList:
    """Test ConditionList model validation."""
    
    def test_valid_condition_list_and(self):
        """Test valid AND condition list."""
        conditions = [
            Condition(field="age", op=">", value=25),
            Condition(field="city", op="=", value="New York")
        ]
        condition_list = ConditionList(mode="AND", filters=conditions)
        assert condition_list.mode == "AND"
        assert len(condition_list.filters) == 2
    
    def test_valid_condition_list_or(self):
        """Test valid OR condition list."""
        conditions = [
            Condition(field="age", op=">", value=25),
            Condition(field="age", op="<", value=35)
        ]
        condition_list = ConditionList(mode="OR", filters=conditions)
        assert condition_list.mode == "OR"
        assert len(condition_list.filters) == 2
    
    def test_condition_list_empty_filters(self):
        """Test condition list with empty filters."""
        with pytest.raises(ValueError):
            ConditionList(mode="AND", filters=[])
    
    def test_condition_list_invalid_mode(self):
        """Test condition list with invalid mode."""
        conditions = [Condition(field="age", op=">", value=25)]
        with pytest.raises(ValidationError):
            ConditionList(mode="INVALID", filters=conditions)


class TestOrderItem:
    """Test OrderItem model validation."""
    
    def test_valid_order_item_ascending(self):
        """Test valid ascending order item."""
        order_item = OrderItem(field="name", ascending=True)
        assert order_item.field == "name"
        assert order_item.ascending is True
    
    def test_valid_order_item_descending(self):
        """Test valid descending order item."""
        order_item = OrderItem(field="age", ascending=False)
        assert order_item.field == "age"
        assert order_item.ascending is False
    
    def test_order_item_default_ascending(self):
        """Test order item with default ascending value."""
        order_item = OrderItem(field="name")
        assert order_item.ascending is True


class TestQuerySpec:
    """Test QuerySpec model validation."""
    
    def test_valid_query_spec_basic(self):
        """Test valid basic query specification."""
        query_spec = QuerySpec(limit=10, offset=0)
        assert query_spec.limit == 10
        assert query_spec.offset == 0
        assert query_spec.order_by is None
        assert query_spec.filter is None
    
    def test_valid_query_spec_with_filter(self):
        """Test valid query specification with filter."""
        filter_condition = Condition(field="age", op=">", value=25)
        query_spec = QuerySpec(limit=10, offset=0, filter=filter_condition)
        assert query_spec.filter == filter_condition
    
    def test_valid_query_spec_with_order_by(self):
        """Test valid query specification with order by."""
        order_items = [
            OrderItem(field="age", ascending=False),
            OrderItem(field="name", ascending=True)
        ]
        query_spec = QuerySpec(limit=10, offset=0, order_by=order_items)
        assert len(query_spec.order_by) == 2
    
    def test_query_spec_invalid_limit(self):
        """Test query specification with invalid limit."""
        with pytest.raises(ValidationError):
            QuerySpec(limit=0, offset=0)  # limit must be >= 1
    
    def test_query_spec_invalid_offset(self):
        """Test query specification with invalid offset."""
        with pytest.raises(ValidationError):
            QuerySpec(limit=10, offset=-1)  # offset must be >= 0


class TestInsertSpec:
    """Test InsertSpec model validation."""
    
    def test_valid_insert_spec(self):
        """Test valid insert specification."""
        payload = {"name": "John", "age": 30, "city": "New York"}
        insert_spec = InsertSpec(payload=payload)
        assert insert_spec.payload == payload
    
    def test_insert_spec_empty_payload(self):
        """Test insert specification with empty payload."""
        insert_spec = InsertSpec(payload={})
        assert insert_spec.payload == {}


class TestUpdateSpec:
    """Test UpdateSpec model validation."""
    
    def test_valid_update_spec(self):
        """Test valid update specification."""
        filter_condition = Condition(field="id", op="=", value=1)
        payload = {"age": 26, "city": "Brooklyn"}
        update_spec = UpdateSpec(filters=filter_condition, payload=payload)
        assert update_spec.filters == filter_condition
        assert update_spec.payload == payload


class TestDeleteSpec:
    """Test DeleteSpec model validation."""
    
    def test_valid_delete_spec(self):
        """Test valid delete specification."""
        filter_condition = Condition(field="id", op="=", value=1)
        delete_spec = DeleteSpec(filters=filter_condition)
        assert delete_spec.filters == filter_condition 