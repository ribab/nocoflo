import sqlite3
import sys
from nicegui import ui, app
from pathlib import Path

# Add root to path for importing common functions
sys.path.append(Path(__file__).parent.parent)

import metadata

@ui.page('/permissions/{table_id}')
def permissions_page(table_id: int):
    """Manage table permissions"""
    if not app.storage.user:
        ui.navigate.to('/login')
        return
    
    # Check if user can manage permissions
    if app.storage.user['role'] != 'admin' and not metadata.has_permission(table_id, 'owner'):
        ui.label('❌ Access denied. Only admins and table owners can manage permissions.')
        ui.link('← Back to tables', '/tables')
        return
    
    # Get table info
    with sqlite3.connect(metadata.METADATA_DB) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT tm.display_name, tm.table_name
            FROM table_meta tm
            WHERE tm.id = ?
        """, (table_id,))
        
        table_info = cursor.fetchone()
        if not table_info:
            ui.label('❌ Table not found')
            return
        
        display_name, table_name = table_info
    
    ui.label(f'🔐 Manage Permissions: {display_name}').classes('text-2xl mb-4')
    
    # Get all users and their current permissions
    with sqlite3.connect(metadata.METADATA_DB) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.id, u.name, u.email, u.role,
                   COALESCE(p.can_read, 0), COALESCE(p.can_write, 0), 
                   COALESCE(p.can_delete, 0), COALESCE(p.is_owner, 0)
            FROM user u
            LEFT JOIN permission p ON u.id = p.user_id AND p.table_id = ?
            ORDER BY u.name
        """, (table_id,))
        
        users = cursor.fetchall()
    
    # Permission form
    ui.label('➕ Grant New Permission').classes('text-lg mb-2')
    
    with ui.card().classes('p-4 mb-6'):
        with ui.row().classes('gap-4 items-end'):
            user_select = ui.select(
                label='Select User',
                options={str(u[0]): f"{u[1]} ({u[2]})" for u in users},
                value=None
            ).classes('w-64')
            
            perm_select = ui.select(
                label='Permission Level',
                options={
                    'read': 'Read Only',
                    'write': 'Read + Write',
                    'delete': 'Read + Write + Delete',
                    'owner': 'Owner (Full Control)'
                },
                value='read'
            ).classes('w-48')
            
            def grant_permission():
                if not user_select.value or not perm_select.value:
                    ui.notify('❌ Please select user and permission level', type='negative')
                    return
                
                user_id = int(user_select.value)
                perm = perm_select.value
                
                # Set permission flags
                can_read = 1
                can_write = 1 if perm in ['write', 'delete', 'owner'] else 0
                can_delete = 1 if perm in ['delete', 'owner'] else 0
                is_owner = 1 if perm == 'owner' else 0
                
                with sqlite3.connect(matadata.METADATA_DB) as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO permission 
                        (user_id, table_id, can_read, can_write, can_delete, is_owner)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (user_id, table_id, can_read, can_write, can_delete, is_owner))
                    conn.commit()
                
                ui.notify('✅ Permission granted successfully')
                ui.navigate.to(f'/permissions/{table_id}')
            
            ui.button('Grant Permission', on_click=grant_permission).classes('bg-green-500 text-white')
    
    # Current permissions table
    ui.label('👥 Current Permissions').classes('text-lg mb-2')
    
    perm_data = []
    for user in users:
        user_id, name, email, role, can_read, can_write, can_delete, is_owner = user
        
        if can_read or can_write or can_delete or is_owner:
            perms = []
            if is_owner:
                perms.append('Owner')
            else:
                if can_read: perms.append('Read')
                if can_write: perms.append('Write') 
                if can_delete: perms.append('Delete')
            
            perm_data.append({
                'User': f"{name} ({email})",
                'Role': role,
                'Permissions': ', '.join(perms) if perms else 'None',
                'Actions': user_id
            })
    
    if perm_data:
        def revoke_permission(user_id):
            with sqlite3.connect(metadata.METADATA_DB) as conn:
                conn.execute("DELETE FROM permission WHERE user_id = ? AND table_id = ?", 
                           (user_id, table_id))
                conn.commit()
            ui.notify('✅ Permission revoked')
            ui.navigate.to(f'/permissions/{table_id}')
        
        with ui.table(
            columns=[
                {'name': 'user', 'label': 'User', 'field': 'User'},
                {'name': 'role', 'label': 'Role', 'field': 'Role'},
                {'name': 'permissions', 'label': 'Permissions', 'field': 'Permissions'},
                {'name': 'actions', 'label': 'Actions', 'field': 'Actions'}
            ],
            rows=perm_data
        ).classes('w-full') as table:
            table.add_slot('body-cell-actions', '''
                <q-td :props="props">
                    <q-btn size="sm" color="negative" label="Revoke" 
                           @click="$parent.$emit('revoke', props.row.Actions)" />
                </q-td>
            ''')
            table.on('revoke', lambda e: revoke_permission(e.args))
    else:
        ui.label('No permissions granted yet.')
    
    ui.link('← Back to table', f'/table/{table_id}').classes('text-blue-500 mt-4')