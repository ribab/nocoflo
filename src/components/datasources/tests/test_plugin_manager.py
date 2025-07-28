"""
Tests for plugin manager and plugin integration.
"""
import pytest
import pluggy
from unittest.mock import Mock, patch
from ..base_datasource import BaseDatasource, hookspec
from ..plugins.sqlite_plugin import SQLiteDataSource, SQLiteConfig
from ..plugins.postgresql_plugin import PostgreSQLDataSource, PostgreSQLConfig
from ..plugins.mysql_plugin import MySQLDataSource, MySQLConfig


class TestPluginManager:
    """Test plugin manager functionality."""
    
    @pytest.fixture
    def plugin_manager(self):
        """Create plugin manager instance."""
        pm = pluggy.PluginManager("datasource")
        import components.datasources.base_datasource
        pm.add_hookspecs(components.datasources.base_datasource)
        return pm
    
    @pytest.fixture
    def sqlite_datasource(self):
        """Create SQLite datasource instance."""
        return SQLiteDataSource()
    
    @pytest.fixture
    def postgresql_datasource(self):
        """Create PostgreSQL datasource instance."""
        return PostgreSQLDataSource()
    
    @pytest.fixture
    def mysql_datasource(self):
        """Create MySQL datasource instance."""
        return MySQLDataSource()
    
    def test_plugin_registration(self, plugin_manager, sqlite_datasource, postgresql_datasource, mysql_datasource):
        """Test plugin registration."""
        # Register plugins
        plugin_manager.register(sqlite_datasource)
        plugin_manager.register(postgresql_datasource)
        plugin_manager.register(mysql_datasource)
        
        # Verify plugins are registered
        plugins = list(plugin_manager.get_plugins())
        assert len(plugins) == 3
        
        # Verify plugin names
        plugin_names = [plugin.name for plugin in plugins]
        assert "sqlite" in plugin_names
        assert "postgresql" in plugin_names
        assert "mysql" in plugin_names
    
    def test_plugin_config_classes(self, sqlite_datasource, postgresql_datasource, mysql_datasource):
        """Test that each plugin has the correct config class."""
        # SQLite
        sqlite_config_class = sqlite_datasource.get_config_class()
        assert sqlite_config_class == SQLiteConfig
        
        # PostgreSQL
        postgresql_config_class = postgresql_datasource.get_config_class()
        assert postgresql_config_class == PostgreSQLConfig
        
        # MySQL
        mysql_config_class = mysql_datasource.get_config_class()
        assert mysql_config_class == MySQLConfig
    
    def test_plugin_config_validation(self, sqlite_datasource, postgresql_datasource, mysql_datasource):
        """Test plugin configuration validation."""
        # SQLite config validation
        sqlite_config = SQLiteConfig(path="/tmp/test.db", table_name="test_table")
        assert sqlite_config.path == "/tmp/test.db"
        assert sqlite_config.table_name == "test_table"
        
        # PostgreSQL config validation
        postgresql_config = PostgreSQLConfig(
            user="test_user", password="test_pass", database="test_db", table_name="test_table"
        )
        assert postgresql_config.user == "test_user"
        assert postgresql_config.database == "test_db"
        
        # MySQL config validation
        mysql_config = MySQLConfig(
            user="test_user", password="test_pass", host="localhost", 
            port=3306, database="test_db", table_name="test_table"
        )
        assert mysql_config.user == "test_user"
        assert mysql_config.host == "localhost"
        assert mysql_config.port == 3306
    
    def test_plugin_hook_implementation(self, plugin_manager, sqlite_datasource, postgresql_datasource, mysql_datasource):
        """Test that plugins implement required hooks."""
        # Register plugins
        plugin_manager.register(sqlite_datasource)
        plugin_manager.register(postgresql_datasource)
        plugin_manager.register(mysql_datasource)
        
        # Check that plugins implement required hooks
        for plugin in [sqlite_datasource, postgresql_datasource, mysql_datasource]:
            assert hasattr(plugin, 'connect')
            assert hasattr(plugin, 'read')
            assert hasattr(plugin, 'insert')
            assert hasattr(plugin, 'update')
            assert hasattr(plugin, 'delete')
    
    def test_plugin_discovery(self, plugin_manager, sqlite_datasource, postgresql_datasource, mysql_datasource):
        """Test plugin discovery functionality."""
        # Register plugins
        plugin_manager.register(sqlite_datasource)
        plugin_manager.register(postgresql_datasource)
        plugin_manager.register(mysql_datasource)
        
        # Get all plugins
        plugins = list(plugin_manager.get_plugins())
        assert len(plugins) == 3
        
        # Verify each plugin has required attributes
        for plugin in plugins:
            assert hasattr(plugin, 'name')
            assert hasattr(plugin, 'get_config_class')
            assert callable(plugin.get_config_class)
    
    def test_plugin_config_matching(self, sqlite_datasource, postgresql_datasource, mysql_datasource):
        """Test plugin configuration matching."""
        # Test SQLite config matching
        sqlite_config_dict = {
            "path": "/tmp/test.db",
            "table_name": "test_table"
        }
        
        # Should match SQLite plugin
        try:
            sqlite_config = sqlite_datasource.get_config_class()(**sqlite_config_dict)
            assert isinstance(sqlite_config, SQLiteConfig)
        except Exception:
            pytest.fail("SQLite config should be valid")
        
        # Test PostgreSQL config matching
        postgresql_config_dict = {
            "user": "test_user",
            "password": "test_pass",
            "database": "test_db",
            "table_name": "test_table"
        }
        
        # Should match PostgreSQL plugin
        try:
            postgresql_config = postgresql_datasource.get_config_class()(**postgresql_config_dict)
            assert isinstance(postgresql_config, PostgreSQLConfig)
        except Exception:
            pytest.fail("PostgreSQL config should be valid")
        
        # Test MySQL config matching
        mysql_config_dict = {
            "user": "test_user",
            "password": "test_pass",
            "host": "localhost",
            "port": 3306,
            "database": "test_db",
            "table_name": "test_table"
        }
        
        # Should match MySQL plugin
        try:
            mysql_config = mysql_datasource.get_config_class()(**mysql_config_dict)
            assert isinstance(mysql_config, MySQLConfig)
        except Exception:
            pytest.fail("MySQL config should be valid")
    
    def test_plugin_config_validation_errors(self, sqlite_datasource, postgresql_datasource, mysql_datasource):
        """Test plugin configuration validation errors."""
        from pydantic import ValidationError
        
        # Test SQLite config validation error
        with pytest.raises(ValidationError):
            sqlite_datasource.get_config_class()(table_name="test_table")  # Missing path
        
        # Test PostgreSQL config validation error
        with pytest.raises(ValidationError):
            postgresql_datasource.get_config_class()(table_name="test_table")  # Missing required fields
        
        # Test MySQL config validation error
        with pytest.raises(ValidationError):
            mysql_datasource.get_config_class()(table_name="test_table")  # Missing required fields


class TestPluginIntegration:
    """Test plugin integration scenarios."""
    
    @pytest.fixture
    def mock_plugin_manager(self):
        """Create mock plugin manager."""
        return Mock()
    
    def test_plugin_selection_by_config(self, sqlite_datasource, postgresql_datasource, mysql_datasource):
        """Test selecting the correct plugin based on configuration."""
        # SQLite config should select SQLite plugin
        sqlite_config = SQLiteConfig(path="/tmp/test.db", table_name="test_table")
        assert sqlite_datasource.get_config_class() == SQLiteConfig
        
        # PostgreSQL config should select PostgreSQL plugin
        postgresql_config = PostgreSQLConfig(
            user="test_user", password="test_pass", database="test_db", table_name="test_table"
        )
        assert postgresql_datasource.get_config_class() == PostgreSQLConfig
        
        # MySQL config should select MySQL plugin
        mysql_config = MySQLConfig(
            user="test_user", password="test_pass", host="localhost", 
            port=3306, database="test_db", table_name="test_table"
        )
        assert mysql_datasource.get_config_class() == MySQLConfig
    
    def test_plugin_hook_compliance(self, sqlite_datasource, postgresql_datasource, mysql_datasource):
        """Test that plugins comply with hook specifications."""
        # Test that all plugins have the required hook methods
        required_hooks = ['connect', 'read', 'insert', 'update', 'delete']
        
        for plugin in [sqlite_datasource, postgresql_datasource, mysql_datasource]:
            for hook_name in required_hooks:
                assert hasattr(plugin, hook_name), f"Plugin {plugin.name} missing hook {hook_name}"
                assert callable(getattr(plugin, hook_name)), f"Plugin {plugin.name} hook {hook_name} is not callable"
    
    def test_plugin_config_inheritance(self, sqlite_datasource, postgresql_datasource, mysql_datasource):
        """Test that plugin configs inherit from base config."""
        from ..base_datasource import BaseDataSourceConfig
        
        # Test SQLite config inheritance
        sqlite_config_class = sqlite_datasource.get_config_class()
        assert issubclass(sqlite_config_class, BaseDataSourceConfig)
        
        # Test PostgreSQL config inheritance
        postgresql_config_class = postgresql_datasource.get_config_class()
        assert issubclass(postgresql_config_class, BaseDataSourceConfig)
        
        # Test MySQL config inheritance
        mysql_config_class = mysql_datasource.get_config_class()
        assert issubclass(mysql_config_class, BaseDataSourceConfig)
    
    def test_plugin_name_uniqueness(self, sqlite_datasource, postgresql_datasource, mysql_datasource):
        """Test that plugin names are unique."""
        plugin_names = [
            sqlite_datasource.name,
            postgresql_datasource.name,
            mysql_datasource.name
        ]
        
        # Check for uniqueness
        assert len(plugin_names) == len(set(plugin_names)), "Plugin names should be unique"
        
        # Verify specific names
        assert "sqlite" in plugin_names
        assert "postgresql" in plugin_names
        assert "mysql" in plugin_names


class TestPluginErrorHandling:
    """Test plugin error handling scenarios."""
    
    def test_invalid_plugin_registration(self, plugin_manager):
        """Test registration of invalid plugin."""
        invalid_plugin = Mock()
        invalid_plugin.name = "invalid"
        
        # Should not raise exception, but plugin should not be registered
        plugin_manager.register(invalid_plugin)
        plugins = list(plugin_manager.get_plugins())
        assert len(plugins) == 0  # Invalid plugin should not be registered
    
    def test_plugin_without_required_methods(self, plugin_manager):
        """Test plugin without required methods."""
        incomplete_plugin = Mock()
        incomplete_plugin.name = "incomplete"
        # Missing required methods
        
        plugin_manager.register(incomplete_plugin)
        plugins = list(plugin_manager.get_plugins())
        assert len(plugins) == 0  # Incomplete plugin should not be registered
    
    def test_plugin_config_validation_failure(self, sqlite_datasource):
        """Test plugin config validation failure."""
        from pydantic import ValidationError
        
        # Test with invalid config
        with pytest.raises(ValidationError):
            sqlite_datasource.get_config_class()(
                # Missing required 'path' field
                table_name="test_table"
            )
    
    def test_plugin_hook_execution_failure(self, sqlite_datasource):
        """Test plugin hook execution failure."""
        # Test with invalid connection
        invalid_config = SQLiteConfig(path="/invalid/path.db", table_name="test_table")
        
        with pytest.raises(Exception):
            sqlite_datasource.connect(invalid_config) 