#!/usr/bin/env python3
"""
Reusable Grid Component using AG Grid in NiceGUI

This component provides a flexible data grid with the following features:
- Configurable columns and data
- Callback functions for various events
- Sorting, filtering, and resizing
- Row selection
- Inline editing (optional)
- Export functionality
- Responsive design

Usage:
    # As a component
    from components.grid import create_grid
    
    grid = create_grid(
        data=your_data,
        column_defs=your_columns,
        on_cell_edit=your_callback,
        on_row_select=your_callback
    )
    
    # Standalone
    python components/grid.py
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from nicegui import ui, app
import pandas as pd
import json

# Add root to path for importing common functions when used as standalone
if __name__ in {"__main__", "__mp_main__"}:
    sys.path.append(str(Path(__file__).parent.parent))

def create_grid(
    data: List[Dict[str, Any]],
    column_defs: Optional[List[Dict[str, Any]]] = None,
    on_cell_edit: Optional[Callable] = None,
    on_row_select: Optional[Callable] = None,
    on_row_double_click: Optional[Callable] = None,
    on_grid_ready: Optional[Callable] = None,
    enable_editing: bool = False,
    enable_selection: bool = True,
    enable_sorting: bool = True,
    enable_filtering: bool = True,
    enable_resizing: bool = True,
    enable_export: bool = True,
    grid_height: str = '500px',
    grid_width: str = '100%',
    theme: str = 'ag-theme-alpine-dark',
    **kwargs
) -> ui.aggrid:
    """
    Create a reusable AG Grid component
    
    Args:
        data: List of dictionaries containing row data
        column_defs: List of column definitions for AG Grid
        on_cell_edit: Callback function for cell edit events
        on_row_select: Callback function for row selection events
        on_row_double_click: Callback function for row double-click events
        on_grid_ready: Callback function when grid is ready
        enable_editing: Whether to enable inline editing
        enable_selection: Whether to enable row selection
        enable_sorting: Whether to enable column sorting
        enable_filtering: Whether to enable column filtering
        enable_resizing: Whether to enable column resizing
        enable_export: Whether to show export buttons
        grid_height: Height of the grid
        grid_width: Width of the grid
        theme: AG Grid theme to use
        **kwargs: Additional arguments to pass to ui.aggrid
    
    Returns:
        ui.aggrid: The configured AG Grid component
    """
    
    # Auto-generate column definitions if not provided
    if column_defs is None and data:
        column_defs = []
        if data:
            sample_row = data[0]
            for key, value in sample_row.items():
                col_def = {
                    'field': key,
                    'headerName': key.replace('_', ' ').title(),
                    'sortable': enable_sorting,
                    'filter': enable_filtering,
                    'resizable': enable_resizing,
                    'editable': enable_editing
                }
                
                # Auto-detect column types
                if isinstance(value, bool):
                    col_def['cellRenderer'] = 'agCheckboxCellRenderer'
                elif isinstance(value, (int, float)):
                    col_def['type'] = 'numericColumn'
                elif isinstance(value, str) and len(value) > 50:
                    col_def['cellRenderer'] = 'agTextCellRenderer'
                    col_def['cellRendererParams'] = {'maxLength': 50}
                
                column_defs.append(col_def)
    
    # Configure grid options
    grid_options = {
        'columnDefs': column_defs or [],
        'rowData': data,
        'defaultColDef': {
            'sortable': enable_sorting,
            'filter': enable_filtering,
            'resizable': enable_resizing,
            'editable': enable_editing
        },
        'rowSelection': 'single' if enable_selection else None,
        'stopEditingWhenCellsLoseFocus': True,
        'animateRows': True,
        'pagination': True,
        'paginationPageSize': 25,
        'domLayout': 'autoHeight',
        'suppressRowClickSelection': False,
        'suppressCellFocus': False,
        'enableCellTextSelection': True,
        'suppressCopyRowsToClipboard': False,
        'suppressExcelExport': False,
        'suppressCsvExport': False,
        **kwargs
    }
    
    # Create container for grid and controls
    with ui.column().classes('w-full'):
        # Export buttons row
        if enable_export and data:
            with ui.row().classes('w-full mb-4 gap-2'):
                ui.button('📊 Export CSV', on_click=lambda: export_csv(data, column_defs)).classes('bg-blue-500 hover:bg-blue-600')
                ui.button('📈 Export Excel', on_click=lambda: export_excel(data, column_defs)).classes('bg-green-500 hover:bg-green-600')
                ui.button('📋 Copy to Clipboard', on_click=lambda: copy_to_clipboard(data)).classes('bg-purple-500 hover:bg-purple-600')
                ui.space()
                ui.label(f'Total Rows: {len(data)}').classes('text-gray-400')
        
        # Create the AG Grid
        grid = ui.aggrid(grid_options).classes(f'{theme}').style(f'height: {grid_height}; width: {grid_width}')
        
        # Set up event handlers
        if on_cell_edit:
            grid.on('cellValueChanged', on_cell_edit)
        
        if on_row_select:
            grid.on('rowSelected', on_row_select)
        
        if on_row_double_click:
            grid.on('rowDoubleClicked', on_row_double_click)
        
        if on_grid_ready:
            grid.on('gridReady', on_grid_ready)
        
        return grid

def export_csv(data: List[Dict[str, Any]], column_defs: Optional[List[Dict[str, Any]]] = None):
    """Export grid data to CSV"""
    if not data:
        ui.notify('No data to export', type='warning')
        return
    
    try:
        df = pd.DataFrame(data)
        csv_content = df.to_csv(index=False)
        
        # Create download link
        ui.download(csv_content, 'grid_data.csv', 'text/csv')
        ui.notify('CSV export started', type='positive')
    except Exception as e:
        ui.notify(f'Export failed: {str(e)}', type='negative')

def export_excel(data: List[Dict[str, Any]], column_defs: Optional[List[Dict[str, Any]]] = None):
    """Export grid data to Excel"""
    if not data:
        ui.notify('No data to export', type='warning')
        return
    
    try:
        df = pd.DataFrame(data)
        
        # Convert to Excel bytes
        import io
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Grid Data')
        
        excel_content = output.getvalue()
        ui.download(excel_content, 'grid_data.xlsx', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        ui.notify('Excel export started', type='positive')
    except Exception as e:
        ui.notify(f'Export failed: {str(e)}', type='negative')

def copy_to_clipboard(data: List[Dict[str, Any]]):
    """Copy grid data to clipboard"""
    if not data:
        ui.notify('No data to copy', type='warning')
        return
    
    try:
        df = pd.DataFrame(data)
        csv_content = df.to_csv(index=False)
        
        # Use JavaScript to copy to clipboard
        ui.run_javascript(f'''
            navigator.clipboard.writeText(`{csv_content}`).then(() => {{
                console.log('Data copied to clipboard');
            }});
        ''')
        ui.notify('Data copied to clipboard', type='positive')
    except Exception as e:
        ui.notify(f'Copy failed: {str(e)}', type='negative')

def demo_grid():
    """Demo function showing various grid configurations"""
    
    # Sample data
    sample_data = [
        {'id': 1, 'name': 'John Doe', 'email': 'john@example.com', 'department': 'Engineering', 'salary': 75000, 'active': True},
        {'id': 2, 'name': 'Jane Smith', 'email': 'jane@example.com', 'department': 'Marketing', 'salary': 65000, 'active': True},
        {'id': 3, 'name': 'Bob Johnson', 'email': 'bob@example.com', 'department': 'Sales', 'salary': 70000, 'active': False},
        {'id': 4, 'name': 'Alice Brown', 'email': 'alice@example.com', 'department': 'Engineering', 'salary': 80000, 'active': True},
        {'id': 5, 'name': 'Charlie Wilson', 'email': 'charlie@example.com', 'department': 'HR', 'salary': 60000, 'active': True},
    ]
    
    # Custom column definitions
    column_defs = [
        {'field': 'id', 'headerName': 'ID', 'width': 80, 'type': 'numericColumn'},
        {'field': 'name', 'headerName': 'Name', 'width': 150, 'editable': True},
        {'field': 'email', 'headerName': 'Email', 'width': 200, 'editable': True},
        {'field': 'department', 'headerName': 'Department', 'width': 150, 'editable': True},
        {'field': 'salary', 'headerName': 'Salary', 'width': 120, 'type': 'numericColumn', 'editable': True},
        {'field': 'active', 'headerName': 'Active', 'width': 100, 'cellRenderer': 'agCheckboxCellRenderer', 'editable': True}
    ]
    
    # Event handlers
    def on_cell_edit(e):
        ui.notify(f'Cell edited: {e.args["colId"]} = {e.args["newValue"]}', type='info')
    
    def on_row_select(e):
        if e.args.get('selected'):
            ui.notify(f'Row selected: {e.args["data"]["name"]}', type='info')
    
    def on_row_double_click(e):
        ui.notify(f'Row double-clicked: {e.args["data"]["name"]}', type='info')
    
    # Create the grid
    return create_grid(
        data=sample_data,
        column_defs=column_defs,
        on_cell_edit=on_cell_edit,
        on_row_select=on_row_select,
        on_row_double_click=on_row_double_click,
        enable_editing=True,
        enable_selection=True,
        grid_height='400px'
    )

# Standalone demo when run directly
if __name__ in {"__main__", "__mp_main__"}:
    # Initialize theme if config is available
    try:
        from config import init_theme
        init_theme()
    except ImportError:
        # Fallback theme configuration
        ui.add_head_html('''
            <script src="https://cdn.tailwindcss.com"></script>
            <style>
                html, body, #app { background-color: #1a1a1a; color: white; }
            </style>
        ''')
    
    @ui.page('/')
    def main_page():
        ui.label('Grid Component Demo').classes('text-2xl mb-8')
        
        with ui.card().classes('mb-8'):
            ui.label('Interactive Data Grid').classes('text-xl mb-4')
            ui.label('This grid demonstrates all features: editing, selection, sorting, filtering, and export.')
            demo_grid()
        
        with ui.card().classes('mb-8'):
            ui.label('Auto-generated Grid').classes('text-xl mb-4')
            ui.label('This grid uses auto-generated column definitions.')
            
            # Auto-generated grid example
            auto_data = [
                {'product': 'Laptop', 'price': 999.99, 'stock': 50, 'category': 'Electronics'},
                {'product': 'Mouse', 'price': 29.99, 'stock': 100, 'category': 'Electronics'},
                {'product': 'Keyboard', 'price': 79.99, 'stock': 75, 'category': 'Electronics'},
            ]
            
            create_grid(
                data=auto_data,
                enable_editing=True,
                grid_height='300px'
            )
    
    ui.run(
        title='Grid Component Demo',
        port=8083,
        reload=True
    ) 