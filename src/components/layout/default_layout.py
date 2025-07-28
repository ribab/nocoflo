from nicegui import ui, app
from typing import Callable, Optional, Dict, List

import metadata
from config import configure_theme
from .base_layout import BaseLayout

class DefaultLayout(BaseLayout):
    """Default layout implementation that provides the standard Nocoflo interface"""
    
    def __init__(self, content_func: Callable, table_id: Optional[int] = None):
        """
        Initialize the default layout
        
        Args:
            content_func: Function to render the main content
            table_id: Optional table ID for table-specific layouts
        """
        super().__init__(content_func, table_id)
        self.left_drawer = None
        self.right_drawer = None
    
    def render(self) -> None:
        """Render the complete layout with navigation, headers, and content"""
        if not app.storage.user:
            ui.navigate.to('/login')
            return

        configure_theme()

        self.left_drawer = ui.left_drawer(bordered=True, elevated=True)
        self.right_drawer = ui.right_drawer(bordered=True, elevated=True)
        self.right_drawer.hide()

        def logout():
            for k in list(app.storage.user):
                del app.storage.user[k]
            ui.navigate.to('/login')

        self.content_func()

        # left_drawer.show()
        with ui.header():
            ui.icon('menu').classes('text-2xl').on('click', lambda: self.left_drawer.toggle())
            ui.space()
            ui.label('Nocoflo').classes('text-2xl')
            ui.space()
            with ui.row():
                ui.label(f'👋 Welcome, {app.storage.user["name"]}!').classes('m-auto')
                if app.storage.user['role'] == 'admin':
                    ui.icon('settings').classes('text-2xl').on('click', lambda: self.right_drawer.toggle())
                ui.icon('logout').classes('text-2xl').on('click', logout)
        
        with self.left_drawer:
            ui.label('Databases').classes('text-xs uppercase text-gray-400 tracking-wide')
            tables = self.get_user_tables()
        
            if not tables:
                ui.label('No tables available. Contact your admin for access.').classes('text-red-400 ml-2')
                return
            
            # Group by database
            db_groups = {}
            for table in tables:
                db_name = table['db_name']
                if db_name not in db_groups:
                    db_groups[db_name] = []
                db_groups[db_name].append(table)
            
            for db_name, db_tables in db_groups.items():
                with ui.expansion(f'{db_name}').classes('w-full mb-4 bg-blue-900 rounded') as db_expansion:
                    for table in db_tables:
                        with ui.row().classes('items-center gap-2 p-0 ml-4 w-full hover:bg-gray-700 rounded transition-all') as row:
                            if self.table_id is not None and table['id'] == self.table_id:
                                ui.a
                                db_expansion.open()
                            ui.icon('table_chart').classes('text-blue-300 text-base')
                            ui.link(f"{table['display_name']}", f"/table/{table['id']}").classes('text-white text-sm flex-1 py-2')
                            ui.icon('more_vert').classes('text-gray-400 hover:text-white cursor-pointer text-base mr-2').on('click', lambda t=table: self.show_table_menu(t))
        
        with self.right_drawer:
            if app.storage.user['role'] == 'admin':
                ui.link('👥 Manage Users', '/admin/users').classes('bg-green-500 text-white p-4 rounded')
                ui.link('✉️ Invite Users', '/admin/invite').classes('bg-purple-500 text-white p-4 rounded')
    
    def get_user_tables(self) -> List[Dict]:
        """
        Get available tables for navigation
        
        Returns:
            List of table metadata dictionaries
        """
        return metadata.get_user_tables()
    
    def show_table_menu(self, table: Dict) -> None:
        """
        Display table-specific menu
        
        Args:
            table: Table metadata dictionary
        """
        # TODO: Implement menu actions (e.g., permissions, rename, delete)
        ui.notify(f"Menu for {table['display_name']}")


# Legacy function for backward compatibility
def layout(content: Callable, table_id: int = None):
    """Legacy layout function for backward compatibility"""
    layout_instance = DefaultLayout(content, table_id)
    layout_instance.render() 