#!/usr/bin/env python3
import sqlite3
import bcrypt
import uuid
from datetime import datetime
from typing import Dict, Optional, List
from nicegui import ui, app
import pandas as pd
from sqlalchemy import create_engine, text
import json
from pathlib import Path
import metadata
import random
import importlib
import os
from config import init_theme

# Initialize theme
init_theme()

# load pages
for page in os.listdir(Path(__file__).parent / 'pages'):
    page = page.split('.')[0]
    importlib.import_module(f'pages.{page}')

# Initialize database and run app
if __name__ in {"__main__", "__mp_main__"}:
    metadata.init_metadata_db()
    
    # Add some sample data for testing
    with sqlite3.connect(metadata.METADATA_DB) as conn:
        cursor = conn.cursor()
        
        # Check if sample DB config exists
        cursor.execute("SELECT COUNT(*) FROM dbconfig")
        if cursor.fetchone()[0] == 0:
            # Create sample database config
            conn.execute("""
                INSERT INTO dbconfig (db_name, con_str, owner_id)
                VALUES ('Sample DB', 'sqlite:///sample_data.db', 1)
            """)
            
            # Create sample table metadata
            conn.execute("""
                INSERT INTO table_meta (table_name, db_id, display_name)
                VALUES ('users', 1, 'Users Table')
            """)
            
            # Create sample external database
            import os
            if not os.path.exists('sample_data.db'):
                sample_engine = create_engine('sqlite:///sample_data.db')
                with sample_engine.connect() as sample_conn:
                    sample_conn.execute(text("""
                        CREATE TABLE users (
                            id INTEGER PRIMARY KEY,
                            name TEXT,
                            email TEXT,
                            department TEXT
                        )
                    """))
                    
                    sample_conn.execute(text("""
                        INSERT INTO users (name, email, department) VALUES
                        ('John Doe', 'john@example.com', 'Engineering'),
                        ('Jane Smith', 'jane@example.com', 'Marketing'),
                        ('Bob Johnson', 'bob@example.com', 'Sales')
                    """))
                    sample_conn.commit()
            
            conn.commit()
    
    ui.run(
        title='NocoClone MVP',
        port=8082,
        reload=True,
        storage_secret=str(random.random())
    ) 