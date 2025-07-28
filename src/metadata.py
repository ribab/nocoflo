from nicegui import app
from typing import Dict, Optional, List
import sqlite3
import bcrypt
from sqlalchemy import create_engine, text

# Database paths
METADATA_DB = "nocoflo.db"



def init_metadata_db():
    """Initialize the metadata database with all required tables"""
    with sqlite3.connect(METADATA_DB) as conn:
        # Users table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'user'
            )
        """)
        
        # Database configurations
        conn.execute("""
            CREATE TABLE IF NOT EXISTS dbconfig (
                id INTEGER PRIMARY KEY,
                db_name TEXT NOT NULL,
                con_str TEXT NOT NULL,
                owner_id INTEGER,
                FOREIGN KEY (owner_id) REFERENCES user(id)
            )
        """)
        
        # Table metadata
        conn.execute("""
            CREATE TABLE IF NOT EXISTS table_meta (
                id INTEGER PRIMARY KEY,
                table_name TEXT NOT NULL,
                db_id INTEGER,
                display_name TEXT,
                FOREIGN KEY (db_id) REFERENCES dbconfig(id)
            )
        """)
        
        # Column metadata
        conn.execute("""
            CREATE TABLE IF NOT EXISTS column_meta (
                id INTEGER PRIMARY KEY,
                table_id INTEGER,
                column_name TEXT NOT NULL,
                display_name TEXT,
                column_type TEXT,
                is_visible INTEGER DEFAULT 1,
                FOREIGN KEY (table_id) REFERENCES table_meta(id)
            )
        """)
        
        # Permissions
        conn.execute("""
            CREATE TABLE IF NOT EXISTS permission (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                table_id INTEGER,
                can_read INTEGER DEFAULT 0,
                can_write INTEGER DEFAULT 0,
                can_delete INTEGER DEFAULT 0,
                is_owner INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES user(id),
                FOREIGN KEY (table_id) REFERENCES table_meta(id)
            )
        """)
        
        # Invite tokens
        conn.execute("""
            CREATE TABLE IF NOT EXISTS invite (
                id INTEGER PRIMARY KEY,
                email TEXT NOT NULL,
                token TEXT UNIQUE NOT NULL,
                used INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Row locks for collaboration
        conn.execute("""
            CREATE TABLE IF NOT EXISTS row_lock (
                id INTEGER PRIMARY KEY,
                table_id INTEGER,
                row_pk TEXT,
                locked_by INTEGER,
                locked_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (locked_by) REFERENCES user(id),
                FOREIGN KEY (table_id) REFERENCES table_meta(id)
            )
        """)
        
        # Change audit log
        conn.execute("""
            CREATE TABLE IF NOT EXISTS changelog (
                id INTEGER PRIMARY KEY,
                table_id INTEGER,
                row_pk TEXT,
                column_name TEXT,
                old_value TEXT,
                new_value TEXT,
                modified_by INTEGER,
                modified_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (modified_by) REFERENCES user(id),
                FOREIGN KEY (table_id) REFERENCES table_meta(id)
            )
        """)
        
        # Create default admin user if not exists
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM user WHERE role = 'admin'")
        if cursor.fetchone()[0] == 0:
            admin_hash = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode()
            conn.execute(
                "INSERT INTO user (name, email, password_hash, role) VALUES (?, ?, ?, ?)",
                ("Admin", "admin@nococlone.com", admin_hash, "admin")
            )
        
        conn.commit()

def get_table_data(table_id: int, limit: int = 100) -> tuple:
    """Get data from external database table"""
    with sqlite3.connect(METADATA_DB) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT tm.table_name, dc.con_str, dc.db_name
            FROM table_meta tm 
            JOIN dbconfig dc ON tm.db_id = dc.id 
            WHERE tm.id = ?
        """, (table_id,))
        
        row = cursor.fetchone()
        if not row:
            return [], []
        
        table_name, con_str, db_name = row
    
    # Use the new datasource manager
    from components.datasources.manager import DataSourceManager
    manager = DataSourceManager()
    
    table_config = {
        'table_id': table_id,
        'table_name': table_name,
        'connection_string': con_str,
        'db_name': db_name
    }
    
    return manager.get_table_data(table_config, limit)


def get_user_by_email(email: str) -> Optional[Dict]:
    """Get user by email"""
    with sqlite3.connect(METADATA_DB) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, email, password_hash, role FROM user WHERE email = ?", (email,))
        row = cursor.fetchone()
        if row:
            return {
                'id': row[0],
                'name': row[1], 
                'email': row[2],
                'password_hash': row[3],
                'role': row[4]
            }
    return None

def has_permission(table_id: int, permission: str) -> bool:
    """Check if current user has permission on table"""
    if not app.storage.user:
        return False
    
    if app.storage.user['role'] == 'admin':
        return True
    
    with sqlite3.connect(METADATA_DB) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT can_read, can_write, can_delete, is_owner 
            FROM permission 
            WHERE user_id = ? AND table_id = ?
        """, (app.storage.user['id'], table_id))
        
        row = cursor.fetchone()
        if not row:
            return False
        
        can_read, can_write, can_delete, is_owner = row
        
        if permission == 'read':
            return can_read or is_owner
        elif permission == 'write':
            return can_write or is_owner
        elif permission == 'delete':
            return can_delete or is_owner
        elif permission == 'owner':
            return is_owner
        
    return False


def get_user_tables() -> List[Dict]:
    """Get tables user has access to"""
    if not app.storage.user:
        return []
    
    with sqlite3.connect(METADATA_DB) as conn:
        cursor = conn.cursor()
        if app.storage.user['role'] == 'admin':
            # Admin sees all tables
            cursor.execute("""
                SELECT tm.id, tm.table_name, tm.display_name, dc.db_name, dc.con_str
                FROM table_meta tm
                JOIN dbconfig dc ON tm.db_id = dc.id
            """)
        else:
            # Regular users see only permitted tables
            cursor.execute("""
                SELECT DISTINCT tm.id, tm.table_name, tm.display_name, dc.db_name, dc.con_str
                FROM table_meta tm
                JOIN dbconfig dc ON tm.db_id = dc.id
                JOIN permission p ON tm.id = p.table_id
                WHERE p.user_id = ? AND (p.can_read = 1 OR p.is_owner = 1)
            """, (app.storage.user['id'],))
        
        tables = []
        for row in cursor.fetchall():
            tables.append({
                'id': row[0],
                'table_name': row[1],
                'display_name': row[2] or row[1],
                'db_name': row[3],
                'con_str': row[4]
            })
        return tables