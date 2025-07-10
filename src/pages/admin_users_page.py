from nicegui import ui, app

@ui.page('/admin/users')
def admin_users():
    """Admin panel for user management"""
    if not app.storage.user or app.storage.user['role'] != 'admin':
        ui.label('❌ Admin access required')
        ui.link('← Back to home', '/')
        return
    
    ui.label('👥 User Management').classes('text-2xl mb-4')
    
    # Get all users
    with sqlite3.connect(metadata.METADATA_DB) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, email, role FROM user ORDER BY name")
        users = cursor.fetchall()
    
    user_data = []
    for user in users:
        user_data.append({
            'ID': user[0],
            'Name': user[1],
            'Email': user[2],
            'Role': user[3],
            'Actions': user[0]
        })
    
    def update_role(user_id, new_role):
        with sqlite3.connect(metadata.METADATA_DB) as conn:
            conn.execute("UPDATE user SET role = ? WHERE id = ?", (new_role, user_id))
            conn.commit()
        ui.notify(f'✅ User role updated to {new_role}')
        ui.navigate.to('/admin/users')
    
    def delete_user(user_id):
        with sqlite3.connect(metadata.METADATA_DB) as conn:
            conn.execute("DELETE FROM user WHERE id = ?", (user_id,))
            conn.execute("DELETE FROM permission WHERE user_id = ?", (user_id,))
            conn.commit()
        ui.notify('✅ User deleted')
        ui.navigate.to('/admin/users')
    
    with ui.table(
        columns=[
            {'name': 'id', 'label': 'ID', 'field': 'ID'},
            {'name': 'name', 'label': 'Name', 'field': 'Name'},
            {'name': 'email', 'label': 'Email', 'field': 'Email'},
            {'name': 'role', 'label': 'Role', 'field': 'Role'},
            {'name': 'actions', 'label': 'Actions', 'field': 'Actions'}
        ],
        rows=user_data
    ).classes('w-full') as table:
        table.add_slot('body-cell-actions', '''
            <q-td :props="props">
                <q-select v-model="role" :options="['user', 'owner', 'admin']" 
                         @update:model-value="$parent.$emit('update_role', props.row.Actions, role)"
                         style="width: 100px; display: inline-block;" />
                <q-btn size="sm" color="negative" label="Delete" class="q-ml-sm"
                       @click="$parent.$emit('delete_user', props.row.Actions)" />
            </q-td>
        ''')
        table.on('update_role', lambda e: update_role(e.args[0], e.args[1]))
        table.on('delete_user', lambda e: delete_user(e.args))

