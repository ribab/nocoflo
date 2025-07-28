import sqlite3
import sys
from nicegui import ui, app
from pathlib import Path
from sqlalchemy import text
from typing import Dict, List, Any

# Add root to path for importing common functions
sys.path.append(str(Path(__file__).parent.parent.parent))

import metadata
from components.grid import create_grid
from .base_view import BaseView

class TableView(BaseView):
    """Table view implementation that displays data in a grid format"""
    
    def __init__(self, table_id: int, datasource: 'BaseDatasource'):
        """
        Initialize the table view
        
        Args:
            table_id: The ID of the table to display
            datasource: The datasource to use for data access
        """
        super().__init__(table_id, datasource)
    
    def render(self) -> None:
        """Render the table view with data from the datasource"""
        if not app.storage.user:
            ui.navigate.to('/login')
            return
        
        if not metadata.has_permission(self.table_id, 'read'):
            ui.label('❌ Access denied to this table.')
            ui.link('← Back to tables', '/tables')
            return
        
        # Get table info
        with sqlite3.connect(metadata.METADATA_DB) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT tm.display_name, tm.table_name, dc.db_name, dc.con_str
                FROM table_meta tm
                JOIN dbconfig dc ON tm.db_id = dc.id
                WHERE tm.id = ?
            """, (self.table_id,))
            
            table_info = cursor.fetchone()
            if not table_info:
                ui.label('❌ Table not found')
                return
            
            display_name, table_name, db_name, con_str = table_info
        
        with ui.row().classes('w-full'):
            ui.label(f'{display_name} ({db_name})')

            ui.space()
        
            # Show user permissions
            if app.storage.user['role'] == 'admin':
                ui.label('🔓 Admin Access: Full permissions').classes('text-green-600 mb-2')
            else:
                perms = []
                if metadata.has_permission(self.table_id, 'read'): perms.append('read')
                if metadata.has_permission(self.table_id, 'write'): perms.append('write')  
                if metadata.has_permission(self.table_id, 'delete'): perms.append('delete')
                if metadata.has_permission(self.table_id, 'owner'): perms.append('owner')
                ui.label(f'🔐 Your access: {", ".join(perms)}').classes('text-blue-600 mb-2')
        
        # Get and display table data
        try:
            # Use the new datasource manager instead of the old datasource
            from components.datasources.manager import DataSourceManager
            manager = DataSourceManager()
            
            table_config = {
                'table_id': self.table_id,
                'table_name': table_name,
                'connection_string': con_str,
                'db_name': db_name
            }
            columns, rows = manager.get_table_data(table_config)
            if not columns:
                ui.label('No data found in table')
                return
            
            # Convert to dict format for AgGrid
            table_data = []
            for row in rows:
                row_dict = {columns[i]: row[i] for i in range(len(columns))}
                table_data.append(row_dict)
            
            # Create AgGrid with editing if user has write permission
            can_edit = metadata.has_permission(self.table_id, 'write') or app.storage.user['role'] == 'admin'
            
            def handle_cell_edit(e):
                """Handle inline cell editing"""
                if not can_edit:
                    ui.notify('❌ No write permission', type='negative')
                    return
                
                row_data = e.args['data']
                pk_col = self._get_primary_key()
                row_pk = str(row_data[pk_col])
                
                # Try to lock row
                if not self._lock_row(row_pk):
                    ui.notify('❌ Row is locked by another user', type='negative')
                    return
                
                # Update the database
                column = e.args['colId']
                new_value = e.args['newValue']
                old_value = e.args['oldValue']
                
                # Update using datasource manager
                table_config = {
                    'table_id': self.table_id,
                    'table_name': table_name,
                    'connection_string': con_str,
                    'db_name': db_name
                }
                if manager.update_cell(table_config, pk_col, row_pk, column, new_value):
                    # Log the change
                    self._log_change(row_pk, column, old_value, new_value)
                    ui.notify('✅ Cell updated', type='positive')
                else:
                    ui.notify('❌ Failed to update cell', type='negative')
                
                # Unlock the row
                self._unlock_row(row_pk)
            
            # Create the grid
            grid = create_grid(
                table_data, 
                on_cell_edit=handle_cell_edit if can_edit else None,
                can_edit=can_edit
            )
            
            # Add row functionality
            if can_edit:
                with ui.row().classes('w-full mt-4'):
                    ui.button('➕ Add Row', on_click=lambda: self._show_add_row_dialog(grid))
                    ui.space()
                    ui.button('🗑️ Delete Selected', on_click=lambda: self._delete_selected_rows(grid))
        
        except Exception as e:
            ui.label(f'❌ Error loading table data: {e}')
    
    def get_view_name(self) -> str:
        """Return human-readable view name"""
        return "Table View"
    
    def can_handle_table(self, table_meta: Dict) -> bool:
        """
        Determine if this view is appropriate for the given table
        
        Args:
            table_meta: Table metadata dictionary
            
        Returns:
            True if this view can handle the table, False otherwise
        """
        # Table view can handle any table
        return True
    
    def get_priority(self) -> int:
        """
        Return selection priority (higher = preferred)
        
        Returns:
            Priority value where higher numbers indicate higher preference
        """
        return 1  # Default priority for table view
    
    def _get_primary_key(self) -> str:
        """Get primary key column for the table"""
        with sqlite3.connect(metadata.METADATA_DB) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT tm.table_name, dc.con_str 
                FROM table_meta tm 
                JOIN dbconfig dc ON tm.db_id = dc.id 
                WHERE tm.id = ?
            """, (self.table_id,))
            
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
    
    def _log_change(self, row_pk: str, column: str, old_val: str, new_val: str):
        """Log a change to the audit trail"""
        with sqlite3.connect(metadata.METADATA_DB) as conn:
            conn.execute("""
                INSERT INTO changelog (table_id, row_pk, column_name, old_value, new_value, modified_by)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (self.table_id, row_pk, column, old_val, new_val, app.storage.user['id']))
            conn.commit()
    
    def _lock_row(self, row_pk: str) -> bool:
        """Try to lock a row for editing"""
        with sqlite3.connect(metadata.METADATA_DB) as conn:
            cursor = conn.cursor()
            # Check if already locked
            cursor.execute("""
                SELECT locked_by FROM row_lock 
                WHERE table_id = ? AND row_pk = ?
            """, (self.table_id, row_pk))
            
            existing = cursor.fetchone()
            if existing and existing[0] != app.storage.user['id']:
                return False  # Already locked by someone else
            
            # Lock it
            conn.execute("""
                INSERT OR REPLACE INTO row_lock (table_id, row_pk, locked_by)
                VALUES (?, ?, ?)
            """, (self.table_id, row_pk, app.storage.user['id']))
            conn.commit()
            return True
    
    def _unlock_row(self, row_pk: str):
        """Unlock a row"""
        with sqlite3.connect(metadata.METADATA_DB) as conn:
            conn.execute("""
                DELETE FROM row_lock 
                WHERE table_id = ? AND row_pk = ? AND locked_by = ?
            """, (self.table_id, row_pk, app.storage.user['id']))
            conn.commit()
    
    def _show_add_row_dialog(self, grid):
        """Show dialog to add a new row"""
        # TODO: Implement add row dialog
        ui.notify('Add row functionality not yet implemented')
    
    def _delete_selected_rows(self, grid):
        """Delete selected rows from the grid"""
        # TODO: Implement delete selected rows
        ui.notify('Delete selected rows functionality not yet implemented') 