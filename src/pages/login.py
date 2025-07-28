import sqlite3
import bcrypt
import sys
from nicegui import ui, app
from pathlib import Path

# Add root to path for importing common functions
sys.path.append(Path(__file__).parent.parent)

import metadata
from components.common.auth import authenticate_user, login_user

@ui.page('/login')
def login():
    """Login page"""
    with ui.card().classes('mx-auto mt-8 p-8'):
        ui.label('🔐 Login to NocoClone').classes('text-2xl mb-4')
        
        email = ui.input('Email').classes('mb-4')
        password = ui.input('Password', password=True).classes('mb-4')
        
        def do_login():
            user = authenticate_user(email.value, password.value)
            if user:
                login_user(user)
                ui.navigate.to('/')
            else:
                ui.notify('❌ Invalid credentials', type='negative')
        
        ui.button('Login', on_click=do_login).classes('bg-blue-500 text-white')
        
        ui.separator().classes('my-4')
        ui.link('📝 Don\'t have an account? Contact admin for invite', '/').classes('text-blue-500')