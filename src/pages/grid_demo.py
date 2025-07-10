#!/usr/bin/env python3
"""
Grid Component Demo Page

This page demonstrates how to use the reusable grid component
in the existing project structure.
"""

import sys
from pathlib import Path
from nicegui import ui, app

# Add root to path for importing components
sys.path.append(str(Path(__file__).parent.parent))

from components.grid import create_grid
from layout_template import layout

def grid_demo_page():
    """Demo page showing the grid component in action"""
    
    if not app.storage.user:
        ui.navigate.to('/login')
        return
    
    # Sample data for demonstration
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
    
    # Page content
    def content():
        ui.label('Grid Component Demo').classes('text-2xl mb-8')
        
        with ui.card().classes('mb-8'):
            ui.label('Interactive Data Grid').classes('text-xl mb-4')
            ui.label('This grid demonstrates all features: editing, selection, sorting, filtering, and export.')
            
            # Create the grid
            create_grid(
                data=sample_data,
                column_defs=column_defs,
                on_cell_edit=on_cell_edit,
                on_row_select=on_row_select,
                on_row_double_click=on_row_double_click,
                enable_editing=True,
                enable_selection=True,
                grid_height='400px'
            )
        
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
    
    layout(content)

@ui.page('/grid-demo')
def render_page():
    """Render the grid demo page"""
    grid_demo_page() 