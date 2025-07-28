import os
import argparse
from typing import Dict, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
else:
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)

from nicegui import ui, app

# Configure default styles for NiceGUI components
def configure_theme():
    """Configure the NiceGUI theme"""
    ui.dark_mode().enable()
    ui.colors(primary='#1976D2')

    # Add Tailwind CSS
    ui.add_head_html('''
        <script src="https://cdn.tailwindcss.com"></script>
        <script>
            tailwind.config = {
                darkMode: 'class',
                theme: {
                    extend: {
                        colors: {
                            dark: {
                                800: '#1f2937',
                                900: '#111827',
                            }
                        }
                    }
                }
            }
        </script>
    ''')

    # Add minimal base styles
    ui.add_head_html('''
        <style>
            html, body, #app, .nicegui-content, .q-page-container, .q-page, .q-layout {
                background-color: #1a1a1a;
                color: white;
            }
            .q-field__native {
                color: white !important;
                background-color: #2d3748 !important;
            }

            .q-field__label {
                color: gray !important;
            }

            .q-field {
                background-color: #2d3748 !important;
            }

            .q-icon {
                color: white !important;
            }

            .q-field__append {
                border: none !important;
            }
        </style>
    ''')

    # Configure default button styles
    ui.button.default_classes('bg-gray-800 hover:bg-gray-700 text-white px-3 py-2 rounded text-sm')
    
    # Configure default label styles
    ui.label.default_classes('text-white')
    
    # Configure default input styles
    ui.input.default_classes('bg-gray-800 text-white border border-gray-700 rounded px-3 py-2')
    
    # Configure default select styles
    ui.select.default_classes('bg-gray-800 text-white border border-gray-700 rounded px-3 py-2')
    
    # Configure default card styles
    ui.card.default_classes('bg-gray-800 text-white border border-gray-700 rounded-lg p-4')
    
    # Configure default table styles
    ui.table.default_classes('bg-gray-800 text-white border border-gray-700 rounded')
    
    # Configure default dialog styles
    ui.dialog.default_classes('bg-gray-900 text-white rounded-lg')
    
    # Configure default drawer styles
    ui.left_drawer.default_classes('bg-gray-900 text-white border-r border-gray-700')
    ui.right_drawer.default_classes('bg-gray-900 text-white border-l border-gray-700')
    
    # Configure default header styles
    ui.header.default_classes('bg-gray-900 text-white border-b border-gray-700 p-4')
    
    # Configure default footer styles
    ui.footer.default_classes('bg-gray-900 text-white border-t border-gray-700 p-4')

def get_metadata_datasource_config() -> Dict[str, str]:
    """
    Get metadata datasource configuration from environment variables or CLI
    
    Returns:
        Dictionary with datasource configuration
    """
    # Default to SQLite
    config = {
        'datasource_type': 'sqlite',
        'connection_string': 'nocoflo.db',
        'host': 'localhost',
        'port': '5432',
        'database': 'nocoflo',
        'username': '',
        'password': ''
    }
    
    # Load from environment variables
    env_mapping = {
        'NOCOFLO_METADATA_DATASOURCE': 'datasource_type',
        'NOCOFLO_METADATA_CONNECTION_STRING': 'connection_string',
        'NOCOFLO_METADATA_HOST': 'host',
        'NOCOFLO_METADATA_PORT': 'port',
        'NOCOFLO_METADATA_DATABASE': 'database',
        'NOCOFLO_METADATA_USERNAME': 'username',
        'NOCOFLO_METADATA_PASSWORD': 'password'
    }
    
    for env_var, config_key in env_mapping.items():
        env_value = os.getenv(env_var)
        if env_value:
            config[config_key] = env_value
    
    # Build connection string based on datasource type
    datasource_type = config['datasource_type']
    if datasource_type == 'sqlite':
        config['connection_string'] = config['connection_string']
    elif datasource_type == 'postgresql':
        username = config['username']
        password = config['password']
        host = config['host']
        port = config['port']
        database = config['database']
        
        if username and password:
            config['connection_string'] = f"postgresql://{username}:{password}@{host}:{port}/{database}"
        else:
            config['connection_string'] = f"postgresql://{host}:{port}/{database}"
    elif datasource_type == 'mysql':
        username = config['username']
        password = config['password']
        host = config['host']
        port = config['port']
        database = config['database']
        
        if username and password:
            config['connection_string'] = f"mysql://{username}:{password}@{host}:{port}/{database}"
        else:
            config['connection_string'] = f"mysql://{host}:{port}/{database}"
    
    return config

def get_metadata_datasource_type() -> str:
    """Get the metadata datasource type"""
    config = get_metadata_datasource_config()
    return config['datasource_type']

def get_metadata_connection_string() -> str:
    """Get the metadata connection string"""
    config = get_metadata_datasource_config()
    return config['connection_string']

def is_metadata_sqlite() -> bool:
    """Check if metadata is using SQLite"""
    return get_metadata_datasource_type() == 'sqlite'

def is_metadata_postgresql() -> bool:
    """Check if metadata is using PostgreSQL"""
    return get_metadata_datasource_type() == 'postgresql'

def is_metadata_mysql() -> bool:
    """Check if metadata is using MySQL"""
    return get_metadata_datasource_type() == 'mysql'

# Call this function at the start of your application
def init_theme():
    # Initialize theme when the app starts
    app.on_startup(configure_theme)

@ui.page('/config-preview')
def config_preview():
    configure_theme()
    """Preview page for all styled components"""
    ui.label('Component Style Preview').classes('text-2xl mb-8')
    
    # Button examples
    with ui.card().classes('mb-8'):
        ui.label('Buttons').classes('text-xl mb-4')
        with ui.row().classes('gap-4'):
            ui.button('Default Button')
            ui.button('Primary Button').classes('bg-blue-500 hover:bg-blue-600')
            ui.button('Success Button').classes('bg-green-500 hover:bg-green-600')
            ui.button('Danger Button').classes('bg-red-500 hover:bg-red-600')
    
    # Input examples
    with ui.card().classes('mb-8'):
        ui.label('Inputs').classes('text-xl mb-4')
        with ui.column().classes('gap-4'):
            ui.input('Text Input').classes('w-64')
            ui.select(['Option 1', 'Option 2', 'Option 3'], value='Option 1').classes('w-64')
    
    # Card example
    with ui.card().classes('mb-8'):
        ui.label('Card').classes('text-xl mb-4')
        ui.label('This is a card with default styling')
    
    # Table example
    with ui.card().classes('mb-8'):
        ui.label('Table').classes('text-xl mb-4')
        columns = [
            {'name': 'Header 1', 'label': 'Header 1', 'field': 'Header 1'},
            {'name': 'Header 2', 'label': 'Header 2', 'field': 'Header 2'}
        ]
        rows = [
            {'Header 1': 'Cell 1', 'Header 2': 'Cell 2'}
        ]
        ui.table(columns=columns, rows=rows).classes('w-full')
    
    # Dialog example
    with ui.card().classes('mb-8'):
        ui.label('Dialog').classes('text-xl mb-4')
        with ui.dialog() as dialog:
            with ui.card():
                ui.label('Dialog Content')
                ui.button('Close', on_click=dialog.close)
        ui.button('Open Dialog', on_click=dialog.open)
    
    # Drawer examples
    with ui.left_drawer() as left_drawer:
        ui.label('Left Drawer Content')
    with ui.right_drawer() as right_drawer:
        ui.label('Right Drawer Content')
    
    with ui.card().classes('mb-8'):
        ui.label('Drawers').classes('text-xl mb-4')
        with ui.row().classes('gap-4'):
            ui.button('Toggle Left', on_click=left_drawer.toggle)
            ui.button('Toggle Right', on_click=right_drawer.toggle)
    
    # Header and Footer example
    with ui.header():
        ui.label('Header Content')
    
    with ui.card().classes('mb-8'):
        ui.label('Header & Footer').classes('text-xl mb-4')
        ui.label('Main Content')
    
    with ui.footer():
        ui.label('Footer Content')