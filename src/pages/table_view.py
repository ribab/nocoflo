import sqlite3
import sys
from nicegui import ui, app
from pathlib import Path
from sqlalchemy import text

# Add root to path for importing common functions
sys.path.append(str(Path(__file__).parent.parent))

import metadata
from layout_template import layout
from components.grid import create_grid

def get_primary_key(table_id: int) -> str:
    """Get primary key column for a table"""
    with sqlite3.connect(metadata.METADATA_DB) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT tm.table_name, dc.con_str 
            FROM table_meta tm 
            JOIN dbconfig dc ON tm.db_id = dc.id 
            WHERE tm.id = ?
        """, (table_id,))
        
        row = cursor.fetchone()
        if not row:
            return 'id'
        
        table_name, con_str = row
    
    engine = metadata.create_engine(con_str)
    with engine.connect() as conn:
        result = conn.execute(text(f"PRAGMA table_info({table_name})"))
        for row in result.fetchall():
            if row[5]:  # pk column
                return row[1]
    
    return 'id'  # fallback

def log_change(table_id: int, row_pk: str, column: str, old_val: str, new_val: str):
    """Log a change to the audit trail"""
    with sqlite3.connect(metadata.METADATA_DB) as conn:
        conn.execute("""
            INSERT INTO changelog (table_id, row_pk, column_name, old_value, new_value, modified_by)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (table_id, row_pk, column, old_val, new_val, app.storage.user['id']))
        conn.commit()

def lock_row(table_id: int, row_pk: str) -> bool:
    """Try to lock a row for editing"""
    with sqlite3.connect(metadata.METADATA_DB) as conn:
        cursor = conn.cursor()
        # Check if already locked
        cursor.execute("""
            SELECT locked_by FROM row_lock 
            WHERE table_id = ? AND row_pk = ?
        """, (table_id, row_pk))
        
        existing = cursor.fetchone()
        if existing and existing[0] != app.storage.user['id']:
            return False  # Already locked by someone else
        
        # Lock it
        conn.execute("""
            INSERT OR REPLACE INTO row_lock (table_id, row_pk, locked_by)
            VALUES (?, ?, ?)
        """, (table_id, row_pk, app.storage.user['id']))
        conn.commit()
        return True

def unlock_row(table_id: int, row_pk: str):
    """Unlock a row"""
    with sqlite3.connect(metadata.METADATA_DB) as conn:
        conn.execute("""
            DELETE FROM row_lock 
            WHERE table_id = ? AND row_pk = ? AND locked_by = ?
        """, (table_id, row_pk, app.storage.user['id']))
        conn.commit()


def table_view(table_id: int):
    """View and edit table data"""
    if not app.storage.user:
        ui.navigate.to('/login')
        return
    
    if not metadata.has_permission(table_id, 'read'):
        ui.label('❌ Access denied to this table.')
        ui.link('← Back to tables', '/tables')
        return
    
    # Get table info
    with sqlite3.connect(metadata.METADATA_DB) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT tm.display_name, tm.table_name, dc.db_name
            FROM table_meta tm
            JOIN dbconfig dc ON tm.db_id = dc.id
            WHERE tm.id = ?
        """, (table_id,))
        
        table_info = cursor.fetchone()
        if not table_info:
            ui.label('❌ Table not found')
            return
        
        display_name, table_name, db_name = table_info
    
    with ui.row().classes('w-full'):
        ui.label(f'{display_name} ({db_name})')

        ui.space()
    
        # Show user permissions
        if app.storage.user['role'] == 'admin':
            ui.label('🔓 Admin Access: Full permissions').classes('text-green-600 mb-2')
        else:
            perms = []
            if metadata.has_permission(table_id, 'read'): perms.append('read')
            if metadata.has_permission(table_id, 'write'): perms.append('write')  
            if metadata.has_permission(table_id, 'delete'): perms.append('delete')
            if metadata.has_permission(table_id, 'owner'): perms.append('owner')
            ui.label(f'🔐 Your access: {", ".join(perms)}').classes('text-blue-600 mb-2')
    
    # Get and display table data
    try:
        columns, rows = metadata.get_table_data(table_id)
        if not columns:
            ui.label('No data found in table')
            return
        
        # Convert to dict format for AgGrid
        table_data = []
        for row in rows:
            row_dict = {columns[i]: row[i] for i in range(len(columns))}
            table_data.append(row_dict)
        
        # Create AgGrid with editing if user has write permission
        can_edit = metadata.has_permission(table_id, 'write') or app.storage.user['role'] == 'admin'
        
        def handle_cell_edit(e):
            """Handle inline cell editing"""
            if not can_edit:
                ui.notify('❌ No write permission', type='negative')
                return
            
            row_data = e.args['data']
            pk_col = get_primary_key(table_id)
            row_pk = str(row_data[pk_col])
            
            # Try to lock row
            if not lock_row(table_id, row_pk):
                ui.notify('❌ Row is locked by another user', type='negative')
                return
            
            # Update the database
            column = e.args['colId']
            new_value = e.args['newValue']
            old_value = e.args['oldValue']
            
            # Get connection string
            with sqlite3.connect(metadata.METADATA_DB) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT dc.con_str, tm.table_name
                    FROM table_meta tm
                    JOIN dbconfig dc ON tm.db_id = dc.id
                    WHERE tm.id = ?
                """, (table_id,))
                con_str, real_table_name = cursor.fetchone()
            
            # Update external database
            engine = metadata.create_engine(con_str)
            with engine.connect() as conn:
                conn.execute(text(f"""
                    UPDATE {real_table_name} 
                    SET {column} = :new_value 
                    WHERE {pk_col} = :pk_value
                """), {'new_value': new_value, 'pk_value': row_pk})
                conn.commit()
            
            # Log the change
            log_change(table_id, row_pk, column, str(old_value), str(new_value))
            
            # Unlock row
            unlock_row(table_id, row_pk)
            
            # Broadcast update to other users
            ui.run_javascript(f'window.dispatchEvent(new CustomEvent("table_updated_{table_id}"))')
            
            ui.notify('✅ Cell updated successfully')
        
        # Create column definitions for the grid
        column_defs = []
        for col in columns:
            col_def = {
                'field': col,
                'headerName': col.replace('_', ' ').title(),
                'editable': can_edit,
                'sortable': True,
                'filter': True,
                'resizable': True
            }
            column_defs.append(col_def)
        
        # Create grid using the reusable component
        grid = create_grid(
            data=table_data,
            column_defs=column_defs,
            on_cell_edit=handle_cell_edit if can_edit else None,
            enable_editing=can_edit,
            enable_selection=can_edit,
            enable_sorting=True,
            enable_filtering=True,
            enable_resizing=True,
            enable_export=True,
            grid_height='100%',
            grid_width='100%',
            theme='ag-theme-balham-dark'
        )
        
        # Add row button
        if can_edit:
            with ui.dialog().classes('bg-transparent') as dialog, ui.card().tight().classes('w-96 max-w-full p-6'):
                with ui.row().classes('w-full border border-white pb-2'):
                    ui.label('Add New Row').classes('text-xl mb-4 mb-0')
                
                inputs = {}
                pk_col = get_primary_key(table_id)
                
                with ui.column().classes('gap-4').classes('w-full'):
                    for col in columns:
                        if col != pk_col:  # Skip primary key
                            inputs[col] = ui.input(col)
                
                def save_row():
                    # Get connection and insert
                    with sqlite3.connect(metadata.METADATA_DB) as conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            SELECT dc.con_str, tm.table_name
                            FROM table_meta tm
                            JOIN dbconfig dc ON tm.db_id = dc.id
                            WHERE tm.id = ?
                        """, (table_id,))
                        con_str, real_table_name = cursor.fetchone()
                    
                    # Insert into external database
                    engine = metadata.create_engine(con_str)
                    with engine.connect() as conn:
                        col_names = ', '.join(inputs.keys())
                        placeholders = ', '.join([f':{col}' for col in inputs.keys()])
                        values = {col: inp.value for col, inp in inputs.items()}
                        
                        conn.execute(text(f"""
                            INSERT INTO {real_table_name} ({col_names})
                            VALUES ({placeholders})
                        """), values)
                        conn.commit()
                    
                    ui.notify('✅ Row added successfully')
                    dialog.close()
                    ui.navigate.to(f'/table/{table_id}')
                
                with ui.row().classes('w-full gap-2 mt-6 justify-end border border-white pt-2'):
                    ui.button('Save', on_click=save_row).classes('bg-green-500 text-white')
                    ui.button('Cancel', on_click=dialog.close).classes('bg-gray-500 text-white')

            with ui.footer():

                def add_row():
                    dialog.open()
                
                ui.space()
                ui.button('➕ Add Row', on_click=add_row).classes('bg-green-500 text-white mt-4')
        
    except Exception as e:
        ui.label(f'❌ Error loading table: {str(e)}')

@ui.page('/table/{table_id}')
def render_page(table_id):
    layout(lambda: table_view(table_id))