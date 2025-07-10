import sqlite3
import sys
from nicegui import ui, app
from pathlib import Path
from typing import List, Dict

# Add root to path for importing common functions
sys.path.append(Path(__file__).parent.parent)

import metadata

@ui.page('/register')
def register(token: str = None):
    """Registration page (invite-only)"""
    
    if not token:
        ui.label('❌ Invalid or missing invite token')
        ui.link('← Back to login', '/login')
        return
    
    # Verify token
    with sqlite3.connect(metadata.METADATA_DB) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT email FROM invite WHERE token = ? AND used = 0", (token,))
        invite_email = cursor.fetchone()
        
        if not invite_email:
            ui.label('❌ Invalid or expired invite token')
            ui.link('← Back to login', '/login')
            return
    
    with ui.card().classes('mx-auto mt-8 p-8'):
        ui.label('📝 Register for NocoClone').classes('text-2xl mb-4')
        ui.label(f'Invited email: {invite_email[0]}').classes('mb-4')
        
        name = ui.input('Full Name').classes('mb-4')
        password = ui.input('Password', password=True).classes('mb-4')
        
        def do_register():
            password_hash = bcrypt.hashpw(password.value.encode(), bcrypt.gensalt()).decode()
            
            with sqlite3.connect(metadata.METADATA_DB) as conn:
                conn.execute("""
                    INSERT INTO user (name, email, password_hash, role)
                    VALUES (?, ?, ?, 'user')
                """, (name.value, invite_email[0], password_hash))
                
                # Mark invite as used
                conn.execute("UPDATE invite SET used = 1 WHERE token = ?", (token,))
                conn.commit()
            
            ui.notify('✅ Account created! Please login.')
            ui.navigate.to('/login')
        
        ui.button('Register', on_click=do_register).classes('bg-green-500 text-white')

@ui.page('/tables')
def tables_page():
    """List all accessible tables"""
    if not app.storage.user:
        ui.navigate.to('/login')
        return
    
    ui.label('📊 Your Tables').classes('text-2xl mb-4')
    
    tables = metadata.get_user_tables()
    
    if not tables:
        ui.label('No tables available. Contact your admin for access.')
        return
    
    # Group by database
    db_groups = {}
    for table in tables:
        db_name = table['db_name']
        if db_name not in db_groups:
            db_groups[db_name] = []
        db_groups[db_name].append(table)
    
    for db_name, db_tables in db_groups.items():
        with ui.expansion(f'🗄️ {db_name}', icon='storage').classes('w-full mb-4'):
            for table in db_tables:
                with ui.row().classes('items-center gap-4 p-2'):
                    ui.link(f"📋 {table['display_name']}", f"/table/{table['id']}")
                    
                    # Show permissions button for owners/admins
                    if app.storage.user['role'] == 'admin' or metadata.has_permission(table['id'], 'owner'):
                        ui.link('🔐 Permissions', f"/permissions/{table['id']}").classes('text-sm bg-gray-200 px-2 py-1 rounded')