from nicegui import ui, app
from typing import Callable

import metadata

from config import configure_theme

def layout(content: Callable, table_id: int = None):
    """Home page - redirect based on auth status"""
    if not app.storage.user:
        ui.navigate.to('/login')
        return

    configure_theme()

    left_drawer = ui.left_drawer(bordered=True, elevated=True)
    right_drawer = ui.right_drawer(bordered=True, elevated=True)
    right_drawer.hide()

    def logout():
        for k in list(app.storage.user):
            del app.storage.user[k]
        ui.navigate.to('/login')

    content()

    # left_drawer.show()
    with ui.header():
        ui.icon('menu').classes('text-2xl').on('click', lambda: left_drawer.toggle())
        ui.space()
        ui.label('Nocoflo').classes('text-2xl')
        ui.space()
        with ui.row():
            ui.label(f'👋 Welcome, {app.storage.user["name"]}!').classes('m-auto')
            if app.storage.user['role'] == 'admin':
                ui.icon('settings').classes('text-2xl').on('click', lambda: right_drawer.toggle())
            ui.icon('logout').classes('text-2xl').on('click', logout)
    
    with left_drawer:
        ui.label('Databases').classes('text-xs uppercase text-gray-400 tracking-wide')
        tables = metadata.get_user_tables()
    
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
                        if table_id is not None and table['id'] == table_id:
                            ui.a
                            db_expansion.open()
                        ui.icon('table_chart').classes('text-blue-300 text-base')
                        ui.link(f"{table['display_name']}", f"/table/{table['id']}").classes('text-white text-sm flex-1 py-2')
                        ui.icon('more_vert').classes('text-gray-400 hover:text-white cursor-pointer text-base mr-2').on('click', lambda t=table: show_table_menu(t))
    
    with right_drawer:
        if app.storage.user['role'] == 'admin':
            ui.link('👥 Manage Users', '/admin/users').classes('bg-green-500 text-white p-4 rounded')
            ui.link('✉️ Invite Users', '/admin/invite').classes('bg-purple-500 text-white p-4 rounded')
        

def show_table_menu(table):
    # TODO: Implement menu actions (e.g., permissions, rename, delete)
    ui.notify(f"Menu for {table['display_name']}")

