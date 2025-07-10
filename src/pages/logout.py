from nicegui import ui, app

@ui.page('/logout')
def logout():
    """Logout page"""
    for k in app.storage.user:
        del app.storage.user[k]
    ui.navigate.to('/login')
