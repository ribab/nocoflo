# User-Defined Preferred Patterns and Preferences

## NiceGUI Framework

### Overview
NiceGUI is a Python framework for building web-based user interfaces with minimal code. It provides a simple way to create interactive web applications using Python.

### Basic Usage Pattern

#### 1. Basic Application Structure
```python
from nicegui import ui

# Create UI elements
ui.label('Hello, NiceGUI!')
ui.button('Click me', on_click=lambda: ui.notify('Button clicked!'))

# Run the application
ui.run()
```

#### 2. Core UI Elements

**Labels and Text**
```python
ui.label('Some text content')
ui.markdown('# Markdown Support')
ui.html('<h1>HTML Content</h1>')
```

**Icons**
```python
# Based on Material Symbols and Icons from Google Fonts
ui.icon('thumb_up', color='primary').classes('text-5xl')
ui.icon('favorite', color='red')
```

**Avatars**
```python
# Square avatar with icon
ui.avatar('favorite_border', text_color='grey-11', square=True)

# Circular avatar with image
ui.avatar('img:https://example.com/image.png', color='blue-2')
```

**Links**
```python
# External link
ui.link('NiceGUI on GitHub', 'https://github.com/zauberzeug/nicegui')

# Internal page anchor
ui.link_target("section_name")  # Create anchor point
ui.link(target="#section_name")  # Link to anchor
```

**Buttons and Interactive Elements**
```python
def handle_click():
    ui.notify('Button clicked!')

ui.button('Click me', on_click=handle_click)
ui.button('Primary Button', color='primary')
ui.button('Secondary Button', color='secondary')
```

**Form Elements**
```python
# Input fields
ui.input('Enter your name', placeholder='Name')
ui.textarea('Description', placeholder='Enter description')

# Select dropdown
ui.select('Choose option', ['Option 1', 'Option 2', 'Option 3'])

# Checkbox and radio buttons
ui.checkbox('Accept terms')
ui.radio('Choose one', ['Option A', 'Option B', 'Option C'])
```

#### 3. Layout and Organization

**Containers and Cards**
```python
with ui.card():
    ui.label('Card Title')
    ui.button('Action')

with ui.row():
    ui.button('Button 1')
    ui.button('Button 2')

with ui.column():
    ui.label('Item 1')
    ui.label('Item 2')
```

**Tabs and Navigation**
```python
with ui.tabs().classes('w-full') as tabs:
    ui.tab('Tab 1')
    ui.tab('Tab 2')

with ui.tab_panels(tabs, value='Tab 1'):
    with ui.tab_panel('Tab 1'):
        ui.label('Content for Tab 1')
    with ui.tab_panel('Tab 2'):
        ui.label('Content for Tab 2')
```

#### 4. Data Binding and State Management

**Reactive Variables**
```python
from nicegui import ui, reactive

# Create reactive variable
count = reactive(0)

def increment():
    count.value += 1

ui.label().bind_text_from(count, backward=lambda x: f'Count: {x}')
ui.button('Increment', on_click=increment)
```

**Data Tables**
```python
from nicegui import ui
import pandas as pd

# Create sample data
data = pd.DataFrame({
    'Name': ['Alice', 'Bob', 'Charlie'],
    'Age': [25, 30, 35],
    'City': ['NYC', 'LA', 'Chicago']
})

ui.table.from_pandas(data)
```

#### 5. Charts and Visualizations

**Plotting with Matplotlib**
```python
import matplotlib.pyplot as plt
import numpy as np

# Create plot
fig, ax = plt.subplots()
x = np.linspace(0, 10, 100)
ax.plot(x, np.sin(x))
ax.set_title('Sine Wave')

# Display in NiceGUI
ui.plotly(fig)
```

**Interactive Charts with Plotly**
```python
import plotly.express as px
import pandas as pd

# Create interactive chart
df = pd.DataFrame({
    'x': [1, 2, 3, 4, 5],
    'y': [2, 4, 1, 5, 3]
})
fig = px.scatter(df, x='x', y='y', title='Interactive Scatter Plot')

ui.plotly(fig)
```

#### 6. Advanced Features

**Custom CSS Classes**
```python
ui.label('Styled text').classes('text-red-500 text-xl font-bold')
ui.button('Custom button').classes('bg-blue-500 hover:bg-blue-700')
```

**Event Handling**
```python
def on_input_change(e):
    ui.notify(f'Input changed to: {e.value}')

ui.input('Type something', on_change=on_input_change)
```

**Async Operations**
```python
import asyncio

async def long_operation():
    await asyncio.sleep(2)
    return "Operation completed!"

async def handle_async_click():
    result = await long_operation()
    ui.notify(result)

ui.button('Run Async Task', on_click=handle_async_click)
```

#### 7. Deployment Options

**Local Development**
```python
ui.run(port=8080, reload=True)  # Development with auto-reload
```

**Production Deployment**
```python
ui.run(port=80, reload=False)  # Production settings
```

**Docker Deployment**
```bash
# Using official Docker image
docker run -it --restart always \
  -p 80:8080 \
  -e PUID=$(id -u) \
  -e PGID=$(id -g) \
  -v $(pwd)/:/app/ \
  zauberzeug/nicegui:latest
```

**Docker Compose**
```yaml
app:
    image: zauberzeug/nicegui:latest
    restart: always
    ports:
        - 80:8080
    environment:
        - PUID=1000
        - PGID=1000
    volumes:
        - ./:/app/
```

**PyInstaller Packaging**
```python
# main.py
from nicegui import native_mode, ui

ui.label('Hello from PyInstaller')
ui.run(reload=False, port=native_mode.find_open_port())

# build.py
import os
import subprocess
from pathlib import Path
import nicegui

cmd = [
    'python',
    '-m', 'PyInstaller',
    'main.py',
    '--name', 'myapp',
    '--onefile',
    '--add-data', f'{Path(nicegui.__file__).parent}{os.pathsep}nicegui'
]
subprocess.call(cmd)
```

**NiceGUI On Air (Remote Sharing)**
```python
# Share your app online for 1 hour
ui.run(on_air=True)

# With registered token for persistent URL
ui.run(on_air='your_token_here')
```

#### 8. Best Practices

**Code Organization**
```python
# Separate UI creation into functions
def create_header():
    with ui.header():
        ui.label('My Application')

def create_sidebar():
    with ui.left_drawer():
        ui.button('Menu Item 1')
        ui.button('Menu Item 2')

def create_main_content():
    with ui.page_sticky():
        ui.label('Main Content Area')

# Main application
def main():
    create_header()
    create_sidebar()
    create_main_content()
    ui.run()

if __name__ == '__main__':
    main()
```

**Error Handling**
```python
def safe_operation():
    try:
        # Your operation here
        result = some_function()
        ui.notify('Success!', type='positive')
    except Exception as e:
        ui.notify(f'Error: {str(e)}', type='negative')

ui.button('Safe Operation', on_click=safe_operation)
```

**Responsive Design**
```python
# Use responsive classes
ui.label('Responsive text').classes('text-sm md:text-lg lg:text-xl')
ui.button('Responsive button').classes('w-full md:w-auto')
```

### Key Advantages
- **Minimal Code**: Create web UIs with very little Python code
- **No HTML/CSS/JS Required**: Pure Python interface
- **Real-time Updates**: Reactive programming model
- **Multiple Deployment Options**: Local, Docker, PyInstaller, cloud
- **Rich Component Library**: Built-in components for common UI patterns
- **Material Design**: Based on Quasar framework with Material Design
- **Async Support**: Full async/await support for complex operations

### Common Use Cases
- **Data Dashboards**: Real-time data visualization
- **Configuration Tools**: Settings and configuration interfaces
- **Monitoring Applications**: System monitoring and control panels
- **Prototyping**: Rapid UI prototyping and testing
- **Internal Tools**: Company internal applications
- **Educational Tools**: Interactive learning applications
