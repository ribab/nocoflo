# Nocoflo Brownfield Enhancement Architecture

## Introduction

This document outlines the architectural approach for enhancing Nocoflo with a component-based architecture and plugin system. Its primary goal is to serve as the guiding architectural blueprint for AI-driven development of new features while ensuring seamless integration with the existing system.

**Relationship to Existing Architecture:**
This document supplements existing project architecture by defining how new components will integrate with current systems. Where conflicts arise between new and existing patterns, this document provides guidance on maintaining consistency while implementing enhancements.

### Existing Project Analysis

#### Current Project State
- **Primary Purpose:** Data exploration and management platform with web-based interface for viewing and editing database tables
- **Current Tech Stack:** Python 3.x, NiceGUI for UI, SQLite as default database, monolithic architecture
- **Architecture Style:** Monolithic structure with tight coupling between UI components and business logic
- **Deployment Method:** Single application deployment with configurable database backend

#### Available Documentation
- Comprehensive refactoring plan with component structure and plugin system design (now integrated into this architecture document)
- docs/prd.md - Product requirements document defining enhancement scope and requirements
- Existing source code structure in src/ directory

#### Identified Constraints
- Must maintain all existing functionality during refactoring
- SQLite database schema must remain compatible as default
- NiceGUI UI framework must be preserved
- Performance impact must be minimal (≤20% memory increase)
- Backward compatibility with existing data and configurations

### Change Log

| Change | Date | Version | Description | Author |
|--------|------|---------|-------------|--------|
| Initial Architecture Creation | 2024-12-19 | 1.0 | Created initial architecture document for Nocoflo refactoring | Winston (Architect) |

## Enhancement Scope and Integration Strategy

### Enhancement Overview
**Enhancement Type:** Major architectural refactoring with plugin system
**Scope:** Transform monolithic structure to component-based architecture with extensible plugin system
**Integration Impact:** Major Impact - requires careful sequencing to maintain system integrity

### Integration Approach
**Code Integration Strategy:** Gradual component extraction with plugin system integration
**Database Integration:** Extend existing metadata tables to support plugin configurations, with SQLite as default but configurable for other databases
**API Integration:** Maintain existing internal API patterns while adding plugin interfaces
**UI Integration:** Component-based approach within existing NiceGUI framework

### Compatibility Requirements
- **Existing API Compatibility:** All existing endpoints must remain functional
- **Database Schema Compatibility:** Extend existing schema without breaking changes
- **UI/UX Consistency:** Maintain existing NiceGUI design patterns
- **Performance Impact:** ≤20% memory usage increase, maintain current performance

## Tech Stack Alignment

### Existing Technology Stack

| Category | Current Technology | Version | Usage in Enhancement | Notes |
|----------|-------------------|---------|---------------------|-------|
| Language | Python | 3.x | Core application and plugin system | Maintain existing version |
| UI Framework | NiceGUI | Latest | Component-based UI integration | Preserve existing UI patterns |
| Database | SQLite (default) | Built-in | Metadata and plugin configuration | Extend schema for plugins, configurable for other databases |
| Plugin System | pluggy | Latest | Plugin management and hooks | New addition for extensibility |
| Testing | pytest | Latest | Component and plugin testing | Extend existing test patterns |

### New Technology Additions

| Technology | Version | Purpose | Rationale | Integration Method |
|------------|---------|---------|-----------|-------------------|
| pluggy | Latest | Plugin management system | Industry standard for Python plugins | Core plugin architecture |
| plotly | Latest | Chart view plugin | Rich data visualization capabilities | Optional plugin dependency |
| psycopg2 | Latest | PostgreSQL datasource | Database connectivity | Optional plugin dependency |
| mysql-connector-python | Latest | MySQL datasource | Database connectivity | Optional plugin dependency |

## Data Models and Schema Changes

### New Data Models

#### Plugin Configuration Model
**Purpose:** Store plugin settings and enable/disable states
**Integration:** Extends existing metadata management system

**Key Attributes:**
- plugin_name: str - Unique identifier for the plugin
- enabled: bool - Whether the plugin is active
- config_json: str - Plugin-specific configuration as JSON
- version: str - Plugin version for compatibility checking

**Relationships:**
- **With Existing:** Links to existing table_meta for table-specific plugin settings
- **With New:** Referenced by plugin_manager for loading and management

#### View Preference Model
**Purpose:** Store user preferences for view types per table
**Integration:** Extends existing user and table metadata

**Key Attributes:**
- table_id: int - Reference to existing table_meta
- user_id: int - Reference to existing user table
- preferred_view: str - Name of preferred view plugin
- view_config_json: str - View-specific configuration as JSON

**Relationships:**
- **With Existing:** Foreign key to table_meta and user tables
- **With New:** Referenced by view selection logic

#### Datasource Configuration Model
**Purpose:** Store connection settings for different datasource types
**Integration:** Extends existing dbconfig table

**Key Attributes:**
- datasource_type: str - Type of datasource (sqlite, postgresql, mysql)
- connection_string: str - Connection parameters
- config_json: str - Datasource-specific configuration
- enabled: bool - Whether this datasource is active

**Relationships:**
- **With Existing:** Extends existing database configuration system
- **With New:** Referenced by datasource plugin manager

### Schema Integration Strategy
**Database Changes Required:**
- **New Tables:** plugin_config, table_view_preference, datasource_config
- **Modified Tables:** dbconfig (add datasource_type and config_json columns)
- **New Indexes:** Indexes on plugin_name, table_id+user_id, datasource_type
- **Migration Strategy:** Additive changes only, no breaking modifications

**Backward Compatibility:**
- All existing data remains accessible through current interfaces
- New columns have default values for existing records
- Existing queries continue to work without modification

## Component Architecture

### New Components

#### Base Layout Component
**Responsibility:** Main layout orchestrator with navigation, headers, drawers
**Integration Points:** UI framework, navigation system, user interface

**Key Interfaces:**
- __init__(content_func, table_id) - Initialize layout with content
- render() - Render the complete layout
- get_user_tables() - Get available tables for navigation
- show_table_menu(table) - Display table-specific menu

**Dependencies:**
- **Existing Components:** NiceGUI UI framework
- **New Components:** Header, left_drawer, right_drawer components

**Technology Stack:** NiceGUI integration, component composition

**Example Implementation:**
```python
class BaseLayout:
    def __init__(self, content_func: Callable, table_id: Optional[int] = None)
    def render(self) -> None
    def get_user_tables(self) -> List[Dict]
    def show_table_menu(self, table: Dict) -> None
```

#### Plugin Manager Component
**Responsibility:** Dynamic plugin loading, registration, and lifecycle management
**Integration Points:** Core application startup, plugin discovery, hook management

**Key Interfaces:**
- load_plugins() - Discover and load available plugins
- get_available_views(table_meta) - Return compatible view plugins
- get_datasource(datasource_type) - Return appropriate datasource plugin
- register_plugin(plugin) - Register new plugin at runtime

**Dependencies:**
- **Existing Components:** metadata.py for configuration storage
- **New Components:** BaseView, BaseDatasource interfaces

**Technology Stack:** pluggy for hook management, Python import system

**Hook Specifications:**
```python
import pluggy

hookspec = pluggy.HookspecMarker("nocoflo")

class ViewHookSpec:
    @hookspec
    def get_view_class(self) -> Type[BaseView]:
        """Return the view class this plugin provides"""
        
    @hookspec  
    def get_view_priority(self) -> int:
        """Return priority for view selection (higher = preferred)"""

class DatasourceHookSpec:
    @hookspec
    def get_datasource_class(self) -> Type[BaseDatasource]:
        """Return the datasource class this plugin provides"""
        
    @hookspec
    def get_supported_schemes(self) -> List[str]:
        """Return list of connection string schemes this datasource supports"""
```

**Example Implementation:**
```python
import pluggy
from .hookspecs import ViewHookSpec, DatasourceHookSpec

class PluginManager:
    def __init__(self):
        self.pm = pluggy.PluginManager("nocoflo")
        self.pm.add_hookspecs(ViewHookSpec)
        self.pm.add_hookspecs(DatasourceHookSpec)
        self.load_default_plugins()
        self.load_external_plugins()
    
    def get_available_views(self, table_meta: Dict) -> List[BaseView]
    def get_datasource(self, datasource_type: str) -> BaseDatasource
    def register_plugin(self, plugin: Any) -> None
```

#### Base View Component
**Responsibility:** Abstract interface for all view types (table, chart, form)
**Integration Points:** Plugin system, UI rendering, data access

**Key Interfaces:**
- render(table_data, config) - Render the view with data
- can_handle_table(table_meta) - Determine if view is appropriate
- get_view_name() - Return human-readable view name
- get_priority() - Return selection priority

**Dependencies:**
- **Existing Components:** NiceGUI UI framework
- **New Components:** Plugin manager, datasource interface

**Technology Stack:** Abstract base class, NiceGUI integration

**Example Implementation:**
```python
class BaseView(ABC):
    def __init__(self, table_id: int, datasource: BaseDatasource)
    
    @abstractmethod
    def render(self) -> None
    
    @abstractmethod
    def get_view_name(self) -> str
    
    @abstractmethod
    def can_handle_table(self, table_meta: Dict) -> bool
```

#### Base Datasource Component
**Responsibility:** Abstract interface for all datasource types (SQLite, PostgreSQL, MySQL)
**Integration Points:** Data access layer, connection management, schema discovery

**Key Interfaces:**
- get_table_data(table_config, limit) - Retrieve data from source
- update_cell(table_config, pk_col, pk_value, column, new_value) - Update data
- get_schema(table_config) - Discover table structure
- test_connection(config) - Validate connection settings

**Dependencies:**
- **Existing Components:** metadata.py for configuration
- **New Components:** Plugin manager, view components

**Technology Stack:** Database drivers, HTTP clients, connection pooling

**Example Implementation:**
```python
class BaseDatasource(ABC):
    @abstractmethod
    def get_table_data(self, table_config: Dict, limit: int = 100) -> Tuple[List[str], List[Tuple]]
    
    @abstractmethod
    def update_cell(self, table_config: Dict, pk_col: str, pk_value: str, column: str, new_value: Any) -> bool
    
    @abstractmethod
    def insert_row(self, table_config: Dict, data: Dict) -> bool
    
    @abstractmethod
    def delete_row(self, table_config: Dict, pk_col: str, pk_value: str) -> bool
    
    @abstractmethod
    def get_schema(self, table_config: Dict) -> List[Dict]
    
    @abstractmethod
    def test_connection(self, connection_config: Dict) -> bool
```

#### Component Interaction Diagram

```mermaid
graph TD
    A[NiceGUI App] --> B[Plugin Manager]
    B --> C[View Plugins]
    B --> D[Datasource Plugins]
    C --> E[Table View]
    C --> F[Chart View]
    C --> G[Form View]
    D --> H[SQLite Datasource]
    D --> I[PostgreSQL Datasource]
    D --> J[MySQL Datasource]
    E --> K[Base View Interface]
    F --> K
    G --> K
    H --> L[Base Datasource Interface]
    I --> L
    J --> L
    K --> M[UI Components]
    L --> N[Data Access Layer]
    M --> O[NiceGUI UI]
    N --> P[Database]
```

## Plugin Examples

### Default Plugins

#### Table View Plugin (`plugins/default/table_view_plugin.py`)
```python
import pluggy
from components.views.base_view import BaseView
from components.views.table_view import TableView

hookimpl = pluggy.HookimplMarker("nocoflo")

class TableViewPlugin:
    @hookimpl
    def get_view_class(self) -> Type[BaseView]:
        return TableView
    
    @hookimpl
    def get_view_priority(self) -> int:
        return 1  # Default fallback priority
```

#### SQLite Datasource Plugin (`plugins/default/sqlite_datasource_plugin.py`)
```python
import pluggy
from components.datasources.base_datasource import BaseDatasource
from components.datasources.sqlite_datasource import SQLiteDatasource

hookimpl = pluggy.HookimplMarker("nocoflo")

class SQLiteDatasourcePlugin:
    @hookimpl
    def get_datasource_class(self) -> Type[BaseDatasource]:
        return SQLiteDatasource
    
    @hookimpl
    def get_supported_schemes(self) -> List[str]:
        return ["sqlite", "sqlite3"]
```

### Extended Plugin Examples

#### Chart View Plugin (`plugins/examples/chart_view_plugin.py`)
```python
class ChartView(BaseView):
    def render(self) -> None:
        # Render charts using plotly/matplotlib
        pass
    
    def can_handle_table(self, table_meta: Dict) -> bool:
        # Check if table has numeric columns suitable for charting
        return self.has_numeric_columns(table_meta)
```

#### Form View Plugin (`plugins/examples/form_view_plugin.py`)
```python
class FormView(BaseView):
    def render(self) -> None:
        # Render as forms for single-record editing
        pass
    
    def can_handle_table(self, table_meta: Dict) -> bool:
        # Good for tables with many columns or complex relationships
        return len(table_meta.get('columns', [])) > 10
```

#### PostgreSQL Datasource Plugin (`plugins/examples/postgres_datasource_plugin.py`)
```python
class PostgreSQLDatasource(BaseDatasource):
    def get_supported_schemes(self) -> List[str]:
        return ["postgresql", "postgres"]
    
    def get_table_data(self, table_config: Dict, limit: int = 100) -> Tuple[List[str], List[Tuple]]:
        # PostgreSQL-specific implementation
        pass
```

## API Design and Integration

### API Integration Strategy
**API Integration Strategy:** Maintain existing internal API patterns while adding plugin interfaces
**Authentication:** Preserve existing authentication system
**Versioning:** No versioning required - additive changes only

### New API Endpoints

#### Plugin Management API
- **Method:** GET
- **Endpoint:** /api/plugins
- **Purpose:** List available plugins and their status
- **Integration:** Extends existing admin functionality

**Request:**
```json
{
  "plugin_type": "view|datasource|all"
}
```

**Response:**
```json
{
  "plugins": [
    {
      "name": "table_view",
      "type": "view",
      "enabled": true,
      "version": "1.0.0"
    }
  ]
}
```

#### View Selection API
- **Method:** POST
- **Endpoint:** /api/tables/{table_id}/view
- **Purpose:** Set preferred view type for table
- **Integration:** Extends existing table management

**Request:**
```json
{
  "view_type": "table|chart|form",
  "config": {}
}
```

**Response:**
```json
{
  "success": true,
  "message": "View preference updated"
}
```

#### Datasource Configuration API
- **Method:** POST
- **Endpoint:** /api/datasources
- **Purpose:** Configure new datasource connection
- **Integration:** Extends existing database configuration

**Request:**
```json
{
  "type": "postgresql",
  "connection_string": "postgresql://user:pass@host:port/db",
  "config": {}
}
```

**Response:**
```json
{
  "success": true,
  "datasource_id": 123
}
```

## Source Tree Integration

### Existing Project Structure
```
nocoflo/
├── src/
│   ├── layout_template.py
│   ├── table_view.py
│   ├── metadata.py
│   └── pages/
│       └── *.py
├── docs/
│   ├── prd.md
│   └── architecture.md
└── plan.md
```

### New File Organization
```
nocoflo/
├── src/
│   ├── components/           # New component architecture
│   │   ├── __init__.py
│   │   ├── layout/
│   │   │   ├── __init__.py
│   │   │   ├── base_layout.py
│   │   │   ├── header.py
│   │   │   ├── left_drawer.py
│   │   │   └── right_drawer.py
│   │   ├── views/
│   │   │   ├── __init__.py
│   │   │   ├── base_view.py
│   │   │   └── table_view.py
│   │   ├── datasources/
│   │   │   ├── __init__.py
│   │   │   ├── base_datasource.py
│   │   │   └── sqlite_datasource.py
│   │   └── common/
│   │       ├── __init__.py
│   │       ├── permissions.py
│   │       ├── locks.py
│   │       └── audit.py
│   ├── plugins/             # New plugin system
│   │   ├── __init__.py
│   │   ├── plugin_manager.py
│   │   ├── hookspecs.py
│   │   ├── default/
│   │   │   ├── __init__.py
│   │   │   ├── table_view_plugin.py
│   │   │   └── sqlite_datasource_plugin.py
│   │   └── external/
│   │       └── __init__.py
│   ├── layout_template.py   # Existing - will be refactored
│   ├── table_view.py        # Existing - will be refactored
│   ├── metadata.py          # Existing - extended for plugins
│   └── pages/               # Existing structure maintained
│       └── *.py
├── docs/
│   ├── prd.md
│   ├── architecture.md
│   └── plugin-development.md
└── plan.md
```

### Integration Guidelines
- **File Naming:** Follow existing Python naming conventions (snake_case)
- **Folder Organization:** Group by functionality (components, plugins, pages)
- **Import/Export Patterns:** Use relative imports within components, absolute imports for external dependencies

### Configuration Updates
**Plugin Configuration (`config.py`):**
```python
PLUGIN_CONFIG = {
    'enabled_plugins': ['table_view', 'sqlite_datasource'],
    'plugin_directories': ['plugins/default', 'plugins/external'],
    'view_selection_strategy': 'auto',  # 'auto', 'manual', 'priority'
}
```

## Infrastructure and Deployment Integration

### Existing Infrastructure
**Current Deployment:** Single Python application with embedded SQLite database
**Infrastructure Tools:** Standard Python deployment (pip, requirements.txt)
**Environments:** Single production environment

### Enhancement Deployment Strategy
**Deployment Approach:** Maintain existing deployment process with plugin discovery
**Infrastructure Changes:** None required - plugin system is self-contained
**Pipeline Integration:** Add plugin validation step to deployment process

### Rollback Strategy
**Rollback Method:** Version control with feature flags for plugin system
**Risk Mitigation:** Gradual rollout with plugin system disabled by default
**Monitoring:** Extend existing logging to include plugin activity

## Coding Standards and Conventions

### Existing Standards Compliance
**Code Style:** PEP 8 with existing project conventions
**Linting Rules:** Extend existing linting to include plugin code
**Testing Patterns:** pytest with component isolation
**Documentation Style:** Docstrings with plugin development examples

### Enhancement-Specific Standards
- **Plugin Development:** Clear interface contracts and error handling
- **Component Isolation:** Minimal dependencies between components
- **Configuration Management:** JSON-based plugin configuration
- **Error Handling:** Graceful degradation when plugins fail

### Critical Integration Rules
- **Existing API Compatibility:** All existing endpoints must remain functional
- **Database Integration:** Additive schema changes only
- **Error Handling:** Plugin failures must not break core functionality
- **Logging Consistency:** Extend existing logging patterns to plugins

## Testing Strategy

### Test-Driven Development (TDD) with pytest

#### TDD Framework and Tools
**Primary Testing Framework:** pytest with comprehensive TDD workflow
**Test Discovery:** pytest automatic test discovery with `test_*.py` and `*_test.py` patterns
**Test Organization:** Hierarchical test structure mirroring component architecture
**Coverage Tool:** pytest-cov for coverage measurement and reporting
**Mocking Framework:** pytest-mock for dependency isolation and component testing

#### TDD Workflow Implementation
**Red-Green-Refactor Cycle:**
1. **Red Phase:** Write failing tests using pytest fixtures and assertions
2. **Green Phase:** Implement minimal code to make tests pass
3. **Refactor Phase:** Improve code while maintaining test coverage

**pytest TDD Configuration:**
```python
# pytest.ini configuration for TDD workflow
[tool:pytest]
testpaths = tests
python_files = test_*.py *_test.py
python_classes = Test*
python_functions = test_*
addopts = 
    --strict-markers
    --disable-warnings
    --cov=src
    --cov-report=term-missing
    --cov-report=html
    --cov-fail-under=90
markers =
    unit: Unit tests for isolated components
    integration: Integration tests for component interactions
    plugin: Plugin-specific tests
    regression: Regression tests for existing functionality
```

#### Component Testing with pytest

**Base Component Test Structure:**
```python
# tests/components/test_base_view.py
import pytest
from unittest.mock import Mock, patch
from src.components.views.base_view import BaseView

class TestBaseView:
    @pytest.fixture
    def mock_datasource(self):
        """Mock datasource for isolated component testing"""
        return Mock()
    
    @pytest.fixture
    def sample_table_meta(self):
        """Sample table metadata for testing"""
        return {
            'id': 1,
            'name': 'test_table',
            'columns': ['id', 'name', 'value']
        }
    
    def test_base_view_initialization(self, mock_datasource):
        """Test that base view can be initialized with datasource"""
        view = BaseView(table_id=1, datasource=mock_datasource)
        assert view.table_id == 1
        assert view.datasource == mock_datasource
    
    def test_base_view_abstract_methods(self):
        """Test that base view requires implementation of abstract methods"""
        with pytest.raises(TypeError):
            BaseView(table_id=1, datasource=Mock())
    
    @pytest.mark.unit
    def test_can_handle_table_interface(self, mock_datasource):
        """Test that can_handle_table method exists and returns boolean"""
        # This test will fail initially (Red phase)
        view = BaseView(table_id=1, datasource=mock_datasource)
        result = view.can_handle_table({})
        assert isinstance(result, bool)
```

**Plugin Testing with pytest:**
```python
# tests/plugins/test_plugin_manager.py
import pytest
from unittest.mock import Mock, patch
from src.plugins.plugin_manager import PluginManager

class TestPluginManager:
    @pytest.fixture
    def plugin_manager(self):
        """Plugin manager instance for testing"""
        return PluginManager()
    
    @pytest.fixture
    def mock_plugin(self):
        """Mock plugin for testing"""
        plugin = Mock()
        plugin.get_view_class.return_value = Mock()
        plugin.get_view_priority.return_value = 1
        return plugin
    
    @pytest.mark.unit
    def test_plugin_registration(self, plugin_manager, mock_plugin):
        """Test that plugins can be registered"""
        plugin_manager.register_plugin(mock_plugin)
        assert mock_plugin in plugin_manager.plugins
    
    @pytest.mark.integration
    def test_plugin_discovery(self, plugin_manager):
        """Test that plugins are discovered from designated directories"""
        with patch('pathlib.Path.glob') as mock_glob:
            mock_glob.return_value = ['test_plugin.py']
            plugin_manager.load_plugins()
            # Verify plugins were loaded
            assert len(plugin_manager.plugins) > 0
```

#### TDD Integration Testing

**Component Interaction Testing:**
```python
# tests/integration/test_view_plugin_integration.py
import pytest
from unittest.mock import Mock, patch
from src.components.views.table_view import TableView
from src.plugins.plugin_manager import PluginManager

class TestViewPluginIntegration:
    @pytest.fixture
    def plugin_manager(self):
        return PluginManager()
    
    @pytest.fixture
    def mock_datasource(self):
        datasource = Mock()
        datasource.get_table_data.return_value = (
            ['id', 'name'], 
            [(1, 'test'), (2, 'example')]
        )
        return datasource
    
    @pytest.mark.integration
    def test_table_view_plugin_integration(self, plugin_manager, mock_datasource):
        """Test that table view plugin integrates with plugin manager"""
        # Get available views through plugin system
        views = plugin_manager.get_available_views({'name': 'test_table'})
        assert len(views) > 0
        
        # Verify table view is available
        table_views = [v for v in views if isinstance(v, TableView)]
        assert len(table_views) > 0
```

#### TDD Regression Testing

**Existing Functionality Preservation:**
```python
# tests/regression/test_existing_functionality.py
import pytest
from src.table_view import TableView  # Existing component

class TestExistingFunctionality:
    @pytest.mark.regression
    def test_existing_table_view_still_works(self):
        """Test that existing table view functionality is preserved"""
        # Test existing table view behavior
        view = TableView(table_id=1, datasource=Mock())
        # Verify existing methods still work
        assert hasattr(view, 'render')
        assert hasattr(view, 'get_table_data')
    
    @pytest.mark.regression
    def test_existing_database_operations(self):
        """Test that existing database operations continue to work"""
        # Test existing database functionality
        # This ensures refactoring doesn't break existing features
        pass
```

### Integration with Existing Tests
**Existing Test Framework:** pytest with existing test patterns
**Test Organization:** Extend existing test structure for components
**Coverage Requirements:** Maintain existing coverage levels

### New Testing Requirements

#### Unit Tests for New Components
- **Framework:** pytest with component isolation
- **Location:** tests/components/, tests/plugins/
- **Coverage Target:** 90% for new components
- **Integration with Existing:** Extend existing test utilities

#### Integration Tests
- **Scope:** Plugin system integration with existing functionality
- **Existing System Verification:** All existing features work with plugin system
- **New Feature Testing:** Plugin loading, view switching, datasource configuration

#### Regression Testing
- **Existing Feature Verification:** Automated tests for all existing functionality
- **Automated Regression Suite:** CI/CD pipeline with plugin system tests
- **Manual Testing Requirements:** User acceptance testing for new view types

## Security Integration

### Existing Security Measures
**Authentication:** Existing user authentication system
**Authorization:** Role-based access control
**Data Protection:** SQLite database with existing security
**Security Tools:** Standard Python security practices

### Enhancement Security Requirements
**New Security Measures:** Plugin sandboxing and validation
**Integration Points:** Plugin authentication and authorization
**Compliance Requirements:** Maintain existing security posture

### Security Testing
**Existing Security Tests:** Extend existing security test suite
**New Security Test Requirements:** Plugin security validation
**Penetration Testing:** Plugin system security assessment

## Next Steps

### Story Manager Handoff
The Nocoflo refactoring project requires careful sequencing to maintain system integrity. The architecture document provides:

- **Component boundaries** that respect existing code structure
- **Plugin system design** that enables extensibility without breaking changes
- **Integration requirements** validated through existing system analysis
- **Risk mitigation strategies** for maintaining existing functionality

**First Story Priority:** Story 1.1 (Component Architecture Foundation) - This establishes the foundation without breaking existing functionality. The component extraction must be done incrementally with comprehensive testing at each step.

**Key Integration Checkpoints:**
- Verify all existing table viewing functionality works after component extraction
- Ensure database operations continue to work with existing data
- Confirm UI navigation and layout remain unchanged from user perspective

### Developer Handoff
Developers implementing this brownfield enhancement should:

- **Reference this architecture document** for component boundaries and integration patterns
- **Follow existing Python coding standards** and project patterns identified in the analysis
- **Implement components incrementally** with comprehensive testing at each step
- **Maintain backward compatibility** with all existing functionality throughout the refactoring
- **Use the plugin system design** to enable extensibility without architectural changes

**Critical Implementation Guidelines:**
- Start with component extraction (Story 1.1) to establish foundation
- Implement plugin system (Story 1.2) with careful testing of existing functionality
- Add new view types (Story 1.3) only after core system is stable
- Extend datasource support (Story 1.4) with proper connection management
- Add management interfaces (Story 1.5) for operational control
- Provide development tools (Story 1.6) for community contribution
- Optimize performance (Story 1.7) to meet requirements

**Risk Mitigation:** Each story includes integration verification steps to ensure existing functionality remains intact. Rollback procedures are defined for each major component change.

### TDD Workflow Integration

#### Development Process with TDD
**Story Implementation Workflow:**
1. **Test Planning:** Define test scenarios for each acceptance criterion
2. **Test Implementation:** Write failing tests using pytest fixtures
3. **Code Implementation:** Implement minimal code to pass tests
4. **Refactoring:** Improve code while maintaining test coverage
5. **Integration Testing:** Test component interactions with existing system
6. **Regression Testing:** Ensure existing functionality remains intact

#### TDD Quality Gates
**Pre-commit Requirements:**
- All tests must pass (pytest exit code 0)
- Test coverage must be ≥90% for new components
- No test warnings or deprecation notices
- All integration tests must pass

**Code Review Requirements:**
- Test coverage reports must be included
- Test quality and maintainability must be reviewed
- Integration test scenarios must be comprehensive
- Regression test coverage must be verified

#### TDD Tools and Automation
**CI/CD Integration:**
```yaml
# .github/workflows/tdd-tests.yml
name: TDD Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.x'
      - name: Install dependencies
        run: |
          pip install pytest pytest-cov pytest-mock
          pip install -r requirements.txt
      - name: Run TDD test suite
        run: |
          pytest --cov=src --cov-report=xml --cov-fail-under=90
      - name: Upload coverage
        uses: codecov/codecov-action@v1
```

## Benefits of This Architecture

1. **Extensibility**: Easy to add new view types and datasources
2. **Maintainability**: Clear separation of concerns
3. **Testability**: Components can be tested in isolation
4. **Reusability**: Components can be reused across different contexts
5. **Community**: Others can contribute plugins without modifying core
6. **Flexibility**: Users can customize their experience with plugin selection

## Implementation Priority

1. **High Priority**: Component structure, plugin manager, default plugins
2. **Medium Priority**: Additional view/datasource plugins, plugin management UI
3. **Low Priority**: Plugin marketplace, advanced configuration options 