from nicegui import ui, app

import metadata
from layout_template import layout

def content():
    ui.label('Click on a database on the left menu to get started...')\
    .style('font-size: 18px')

@ui.page('/')
def home():
    """Home page - redirect based on auth status"""
    layout(content)    

