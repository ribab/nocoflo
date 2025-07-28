# Datasource Plugin Test Plan

## Overview

This test plan outlines the comprehensive testing strategy for the datasource plugins (SQLite, PostgreSQL, MySQL) following the plugin architecture defined in `PLAN.md`. The tests will validate the pluggy-based plugin system, Pydantic configuration validation, and CRUD operations across all supported datasources.

## Test Environment Setup

### 1. Temporary Environment Strategy

#### SQLite Testing
- **In-Memory Database**: Use `:memory:` for fast, isolated tests
- **Temporary File Database**: Use `tempfile.NamedTemporaryFile()` for file-based tests
- **Cleanup**: Automatic cleanup via pytest fixtures and context managers
- **Advantages**: No external dependencies, fast execution, isolated tests

#### PostgreSQL Testing
- **Docker Container**: Use `pytest-docker` or `testcontainers` for isolated PostgreSQL instances
- **Mock Strategy**: Mock SQLAlchemy connections for unit tests
- **Integration Tests**: Real PostgreSQL container for end-to-end testing
- **Configuration**: Environment variables for connection details

#### MySQL Testing
- **Docker Container**: Use `pytest-docker` or `testcontainers` for isolated MySQL instances
- **Mock Strategy**: Mock SQLAlchemy connections for unit tests
- **Integration Tests**: Real MySQL container for end-to-end testing
- **Configuration**: Environment variables for connection details

### 2. Test Data Management

#### Sample Data Structure
```python
SAMPLE_DATA = [
    {"id": 1, "name": "Alice", "age": 25, "city": "New York"},
    {"id": 2, "name": "Bob", "age": 30, "city": "Los Angeles"},
    {"id": 3, "name": "Charlie", "age": 35, "city": "Chicago"},
    {"id": 4, "name": "Diana", "age": 28, "city": "Houston"},
    {"id": 5, "name": "Eve", "age": 32, "city": "Phoenix"}
]
```

#### Test Table Schema
```sql
CREATE TABLE test_table (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    age INTEGER,
    city TEXT
);
```

## Test Organization

### 1. Test File Structure
```
src/components/datasources/tests/
├── __init__.py
├── conftest.py                    # Common fixtures
├── test_base_datasource.py        # Base class and hook specifications
├── test_sqlite_plugin.py          # SQLite plugin tests
├── test_postgresql_plugin.py      # PostgreSQL plugin tests
├── test_mysql_plugin.py           # MySQL plugin tests
├── test_plugin_manager.py         # Plugin manager integration tests
├── test_configuration.py          # Pydantic configuration tests
└── integration/                   # Integration test suite
    ├── test_crud_operations.py
    ├── test_query_building.py
    └── test_error_handling.py
```

### 2. Test Categories

#### Unit Tests
- **Plugin Hook Implementation**: Test each hook method independently
- **Configuration Validation**: Test Pydantic model validation
- **Query Building**: Test SQL generation for different query types
- **Error Handling**: Test error scenarios and edge cases

#### Integration Tests
- **CRUD Operations**: End-to-end create, read, update, delete operations
- **Complex Queries**: Multi-condition filters, ordering, pagination
- **Transaction Handling**: Commit/rollback scenarios
- **Connection Management**: Connection lifecycle and cleanup

#### Plugin System Tests
- **Plugin Discovery**: Test pluggy plugin loading and registration
- **Hook Execution**: Test hook specification compliance
- **Plugin Manager**: Test datasource selection and configuration

## Test Implementation Strategy

### 1. Fixture-Based Testing

#### Common Fixtures (conftest.py)
- `temp_sqlite_db`: Temporary SQLite database
- `mock_connection`: Mock database connection
- `sample_data`: Standard test dataset
- `query_specs`: Various query specifications
- `config_fixtures`: Database-specific configurations

#### Plugin-Specific Fixtures
- SQLite: In-memory and file-based database fixtures
- PostgreSQL: Docker container and mock connection fixtures
- MySQL: Docker container and mock connection fixtures

### 2. Test Coverage Areas

#### Configuration Testing
```python
def test_sqlite_config_validation():
    """Test SQLite configuration validation"""
    
def test_postgresql_config_validation():
    """Test PostgreSQL configuration validation"""
    
def test_mysql_config_validation():
    """Test MySQL configuration validation"""
```

#### Connection Testing
```python
def test_sqlite_connection():
    """Test SQLite connection establishment"""
    
def test_postgresql_connection():
    """Test PostgreSQL connection establishment"""
    
def test_mysql_connection():
    """Test MySQL connection establishment"""
```

#### CRUD Operation Testing
```python
def test_insert_operation():
    """Test data insertion across all plugins"""
    
def test_read_operation():
    """Test data retrieval across all plugins"""
    
def test_update_operation():
    """Test data update across all plugins"""
    
def test_delete_operation():
    """Test data deletion across all plugins"""
```

#### Query Building Testing
```python
def test_simple_query():
    """Test basic SELECT queries"""
    
def test_filtered_query():
    """Test queries with WHERE clauses"""
    
def test_ordered_query():
    """Test queries with ORDER BY clauses"""
    
def test_complex_filter_query():
    """Test queries with complex AND/OR conditions"""
    
def test_pagination_query():
    """Test queries with LIMIT and OFFSET"""
```

#### Error Handling Testing
```python
def test_invalid_configuration():
    """Test handling of invalid configurations"""
    
def test_connection_failure():
    """Test handling of connection failures"""
    
def test_query_syntax_error():
    """Test handling of SQL syntax errors"""
    
def test_data_type_mismatch():
    """Test handling of data type mismatches"""
```

### 3. Mock Strategy

#### Database Connection Mocking
```python
@pytest.fixture
def mock_sqlite_connection():
    """Mock SQLite connection with realistic behavior"""
    
@pytest.fixture
def mock_postgresql_connection():
    """Mock PostgreSQL connection with realistic behavior"""
    
@pytest.fixture
def mock_mysql_connection():
    """Mock MySQL connection with realistic behavior"""
```

#### Result Set Mocking
```python
@pytest.fixture
def mock_result_set():
    """Mock database result set with sample data"""
```

## Test Execution Strategy

### 1. Test Isolation
- **Database Isolation**: Each test uses a fresh database instance
- **Connection Isolation**: Each test gets a new connection
- **Data Isolation**: Each test starts with clean test data
- **Plugin Isolation**: Each plugin test runs independently

### 2. Test Execution Order
1. **Unit Tests**: Fast, isolated tests for individual components
2. **Integration Tests**: End-to-end tests with real databases
3. **Plugin System Tests**: Tests for plugin discovery and management
4. **Performance Tests**: Tests for query performance and optimization

### 3. Test Data Management
- **Setup**: Initialize test data before each test
- **Teardown**: Clean up test data after each test
- **Fixtures**: Reusable test data and database setups
- **Factories**: Dynamic test data generation

## Environment Configuration

### 1. Development Environment
```bash
# Install test dependencies
pip install pytest pytest-docker testcontainers

# Set up environment variables
export POSTGRES_TEST_HOST=localhost
export POSTGRES_TEST_PORT=5432
export POSTGRES_TEST_USER=test_user
export POSTGRES_TEST_PASSWORD=test_password
export POSTGRES_TEST_DB=test_db

export MYSQL_TEST_HOST=localhost
export MYSQL_TEST_PORT=3306
export MYSQL_TEST_USER=test_user
export MYSQL_TEST_PASSWORD=test_password
export MYSQL_TEST_DB=test_db
```

### 2. CI/CD Environment
```yaml
# GitHub Actions or similar CI configuration
services:
  postgres:
    image: postgres:13
    env:
      POSTGRES_USER: test_user
      POSTGRES_PASSWORD: test_password
      POSTGRES_DB: test_db
    ports:
      - 5432:5432
      
  mysql:
    image: mysql:8.0
    env:
      MYSQL_ROOT_PASSWORD: root_password
      MYSQL_DATABASE: test_db
      MYSQL_USER: test_user
      MYSQL_PASSWORD: test_password
    ports:
      - 3306:3306
```

## Test Metrics and Quality Gates

### 1. Coverage Requirements
- **Line Coverage**: Minimum 90% for all plugin files
- **Branch Coverage**: Minimum 85% for conditional logic
- **Function Coverage**: 100% for all public methods
- **Plugin Hook Coverage**: 100% for all hook implementations

### 2. Performance Requirements
- **Test Execution Time**: Unit tests < 1 second each
- **Integration Test Time**: < 30 seconds for full suite
- **Memory Usage**: < 100MB per test process
- **Database Setup Time**: < 5 seconds per test

### 3. Quality Gates
- **All Tests Pass**: No failing tests
- **Coverage Threshold**: Meet minimum coverage requirements
- **Performance Threshold**: Meet performance requirements
- **Code Quality**: No linting errors or warnings

## Risk Mitigation

### 1. External Dependencies
- **Docker Fallback**: Use mock connections if Docker unavailable
- **Database Fallback**: Skip integration tests if databases unavailable
- **Network Issues**: Timeout handling for remote database connections

### 2. Test Data Integrity
- **Unique Test Data**: Use UUIDs or timestamps for unique identifiers
- **Data Cleanup**: Ensure proper cleanup in all test scenarios
- **Transaction Rollback**: Use database transactions for test isolation

### 3. Platform Compatibility
- **Cross-Platform**: Ensure tests work on Linux, macOS, Windows
- **Python Version**: Test on Python 3.8, 3.9, 3.10, 3.11
- **Database Version**: Test with multiple database versions

## Implementation Timeline

### Phase 1: Foundation (Day 1)
- [ ] Set up test directory structure
- [ ] Create common fixtures (conftest.py)
- [ ] Implement base datasource tests
- [ ] Set up CI/CD environment

### Phase 2: SQLite Plugin (Day 2)
- [ ] Implement SQLite unit tests
- [ ] Test configuration validation
- [ ] Test CRUD operations
- [ ] Test query building

### Phase 3: PostgreSQL Plugin (Day 3)
- [ ] Implement PostgreSQL unit tests
- [ ] Set up Docker container testing
- [ ] Test SQLAlchemy integration
- [ ] Test complex query scenarios

### Phase 4: MySQL Plugin (Day 4)
- [ ] Implement MySQL unit tests
- [ ] Test MySQL-specific features
- [ ] Test connection pooling
- [ ] Test transaction handling

### Phase 5: Integration & Performance (Day 5)
- [ ] Implement integration tests
- [ ] Performance benchmarking
- [ ] Error handling validation
- [ ] Documentation and cleanup

## Success Criteria

1. **Complete Coverage**: All plugin hooks and methods tested
2. **Reliable Execution**: Tests pass consistently across environments
3. **Fast Execution**: Test suite completes in under 2 minutes
4. **Maintainable**: Clear, well-documented test code
5. **Extensible**: Easy to add new plugins and test scenarios

This test plan ensures comprehensive validation of the datasource plugin architecture while maintaining high code quality and test reliability. 