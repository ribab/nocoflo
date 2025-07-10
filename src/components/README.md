# Grid Component

A reusable AG Grid component for NiceGUI applications that provides a flexible data grid with advanced features.

## Features

- **Configurable Columns**: Auto-generate or define custom column definitions
- **Event Callbacks**: Handle cell edits, row selection, double-clicks, and grid ready events
- **Export Functionality**: Export to CSV, Excel, or copy to clipboard
- **Interactive Features**: Sorting, filtering, resizing, and inline editing
- **Responsive Design**: Adapts to different screen sizes
- **Theme Support**: Uses dark theme by default (matches project theme)
- **Standalone Mode**: Can be run independently for testing

## Installation

Make sure you have the required dependencies:

```bash
pip install nicegui pandas openpyxl
```

## Usage

### Basic Usage

```python
from components.grid import create_grid

# Sample data
data = [
    {'id': 1, 'name': 'John Doe', 'email': 'john@example.com'},
    {'id': 2, 'name': 'Jane Smith', 'email': 'jane@example.com'},
]

# Create grid with auto-generated columns
grid = create_grid(data=data)
```

### Advanced Usage with Custom Columns

```python
from components.grid import create_grid

# Custom column definitions
column_defs = [
    {'field': 'id', 'headerName': 'ID', 'width': 80, 'type': 'numericColumn'},
    {'field': 'name', 'headerName': 'Name', 'width': 150, 'editable': True},
    {'field': 'email', 'headerName': 'Email', 'width': 200, 'editable': True},
    {'field': 'active', 'headerName': 'Active', 'cellRenderer': 'agCheckboxCellRenderer'},
]

# Event handlers
def on_cell_edit(e):
    print(f"Cell edited: {e.args['colId']} = {e.args['newValue']}")

def on_row_select(e):
    if e.args.get('selected'):
        print(f"Row selected: {e.args['data']['name']}")

# Create grid with custom configuration
grid = create_grid(
    data=data,
    column_defs=column_defs,
    on_cell_edit=on_cell_edit,
    on_row_select=on_row_select,
    enable_editing=True,
    enable_selection=True,
    grid_height='500px'
)
```

## Parameters

### Required Parameters

- `data` (List[Dict[str, Any]]): List of dictionaries containing row data

### Optional Parameters

- `column_defs` (List[Dict[str, Any]]): Custom column definitions for AG Grid
- `on_cell_edit` (Callable): Callback function for cell edit events
- `on_row_select` (Callable): Callback function for row selection events
- `on_row_double_click` (Callable): Callback function for row double-click events
- `on_grid_ready` (Callable): Callback function when grid is ready
- `enable_editing` (bool): Whether to enable inline editing (default: False)
- `enable_selection` (bool): Whether to enable row selection (default: True)
- `enable_sorting` (bool): Whether to enable column sorting (default: True)
- `enable_filtering` (bool): Whether to enable column filtering (default: True)
- `enable_resizing` (bool): Whether to enable column resizing (default: True)
- `enable_export` (bool): Whether to show export buttons (default: True)
- `grid_height` (str): Height of the grid (default: '500px')
- `grid_width` (str): Width of the grid (default: '100%')
- `theme` (str): AG Grid theme to use (default: 'ag-theme-alpine-dark')

## Event Handlers

### Cell Edit Event

```python
def on_cell_edit(e):
    # e.args contains:
    # - 'data': The row data
    # - 'colId': The column field name
    # - 'newValue': The new value
    # - 'oldValue': The old value
    pass
```

### Row Selection Event

```python
def on_row_select(e):
    # e.args contains:
    # - 'data': The row data
    # - 'selected': Whether the row is selected
    pass
```

### Row Double-Click Event

```python
def on_row_double_click(e):
    # e.args contains:
    # - 'data': The row data
    pass
```

## Column Definitions

Column definitions follow the AG Grid specification. Common properties:

- `field`: The data field name
- `headerName`: Display name for the column header
- `width`: Column width in pixels
- `editable`: Whether the column is editable
- `sortable`: Whether the column is sortable
- `filter`: Whether the column has filtering
- `type`: Column type ('numericColumn', 'dateColumn', etc.)
- `cellRenderer`: Custom cell renderer

### Auto-Generated Columns

If no column definitions are provided, the component will auto-generate them based on the data:

- Boolean values get checkbox renderers
- Numeric values get numeric column type
- Long strings get text renderers with truncation
- All columns get basic sorting, filtering, and resizing

## Export Features

The grid includes built-in export functionality:

- **CSV Export**: Downloads data as CSV file
- **Excel Export**: Downloads data as Excel file (requires openpyxl)
- **Copy to Clipboard**: Copies data to system clipboard

## Standalone Mode

You can run the grid component independently for testing:

```bash
python components/grid.py
```

This will start a demo server on port 8083 with example grids.

## Integration with Project

The grid component is designed to work seamlessly with the existing project structure:

1. Uses the project's dark theme
2. Follows the same styling patterns
3. Integrates with the layout system
4. Supports the authentication system

## Demo Page

A demo page is available at `/grid-demo` that shows various grid configurations and features.

## Examples

See `pages/grid_demo.py` for a complete example of how to use the grid component within the project structure. 