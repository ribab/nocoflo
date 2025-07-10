from nicegui import ui, app

@ui.page('/admin/invite')
def admin_invite():
    """Admin panel for sending invites"""
    if not app.storage.user or app.storage.user['role'] != 'admin':
        ui.label('❌ Admin access required')
        ui.link('← Back to home', '/')
        return
    
    ui.label('✉️ Invite New Users').classes('text-2xl mb-4')
    
    with ui.card().classes('p-4'):
        email = ui.input('Email address').classes('w-full mb-4')
        
        def send_invite():
            if not email.value:
                ui.notify('❌ Please enter an email address', type='negative')
                return
            
            # Generate unique token
            token = str(uuid.uuid4())
            
            with sqlite3.connect(metadata.METADATA_DB) as conn:
                conn.execute("""
                    INSERT INTO invite (email, token)
                    VALUES (?, ?)
                """, (email.value, token))
                conn.commit()
            
            # Create invite link
            invite_link = f"http://localhost:8082/register?token={token}"
            
            ui.notify(f'✅ Invite created! Send this link: {invite_link}')
            
            # Show the invite link
            with ui.dialog() as dialog:
                ui.label('📧 Invite Link Created').classes('text-xl mb-4')
                ui.label(f'Email: {email.value}').classes('mb-2')
                ui.input(
                    'Invite Link',
                    value=invite_link,
                    # readonly=True
                ).classes('w-full mb-4')
                ui.button('Copy Link', on_click=lambda: ui.run_javascript(f'navigator.clipboard.writeText("{invite_link}")'))
                ui.button('Close', on_click=dialog.close)
            
            dialog.open()
            email.value = ''
        
        ui.button('Create Invite', on_click=send_invite).classes('bg-green-500 text-white')