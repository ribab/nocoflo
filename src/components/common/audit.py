import sqlite3
from nicegui import app
from typing import Dict, List, Optional
from datetime import datetime

import metadata

def log_change(table_id: int, row_pk: str, column: str, old_value: str, new_value: str, user_id: Optional[int] = None) -> bool:
    """
    Log a change to the audit trail
    
    Args:
        table_id: ID of the table being modified
        row_pk: Primary key value of the modified row
        column: Name of the column being modified
        old_value: Previous value
        new_value: New value
        user_id: ID of the user making the change (defaults to current user)
        
    Returns:
        True if change was logged successfully, False otherwise
    """
    try:
        if user_id is None and app.storage.user:
            user_id = app.storage.user['id']
        
        with sqlite3.connect(metadata.METADATA_DB) as conn:
            conn.execute("""
                INSERT INTO changelog (table_id, row_pk, column_name, old_value, new_value, modified_by, modified_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (table_id, row_pk, column, old_value, new_value, user_id, datetime.now().isoformat()))
            conn.commit()
        
        return True
    except Exception as e:
        print(f"Error logging change: {e}")
        return False

def get_changelog(table_id: int, limit: int = 100) -> List[Dict]:
    """
    Get changelog entries for a table
    
    Args:
        table_id: ID of the table
        limit: Maximum number of entries to return
        
    Returns:
        List of changelog entry dictionaries
    """
    try:
        with sqlite3.connect(metadata.METADATA_DB) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT cl.row_pk, cl.column_name, cl.old_value, cl.new_value, 
                       cl.modified_by, cl.modified_at, u.name as user_name
                FROM changelog cl
                LEFT JOIN user u ON cl.modified_by = u.id
                WHERE cl.table_id = ?
                ORDER BY cl.modified_at DESC
                LIMIT ?
            """, (table_id, limit))
            
            entries = []
            for row in cursor.fetchall():
                entries.append({
                    'row_pk': row[0],
                    'column_name': row[1],
                    'old_value': row[2],
                    'new_value': row[3],
                    'modified_by': row[4],
                    'modified_at': row[5],
                    'user_name': row[6] or 'Unknown'
                })
            
            return entries
    except Exception as e:
        print(f"Error getting changelog: {e}")
        return []

def get_row_changelog(table_id: int, row_pk: str) -> List[Dict]:
    """
    Get changelog entries for a specific row
    
    Args:
        table_id: ID of the table
        row_pk: Primary key value of the row
        
    Returns:
        List of changelog entry dictionaries for the row
    """
    try:
        with sqlite3.connect(metadata.METADATA_DB) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT cl.column_name, cl.old_value, cl.new_value, 
                       cl.modified_by, cl.modified_at, u.name as user_name
                FROM changelog cl
                LEFT JOIN user u ON cl.modified_by = u.id
                WHERE cl.table_id = ? AND cl.row_pk = ?
                ORDER BY cl.modified_at DESC
            """, (table_id, row_pk))
            
            entries = []
            for row in cursor.fetchall():
                entries.append({
                    'column_name': row[0],
                    'old_value': row[1],
                    'new_value': row[2],
                    'modified_by': row[3],
                    'modified_at': row[4],
                    'user_name': row[5] or 'Unknown'
                })
            
            return entries
    except Exception as e:
        print(f"Error getting row changelog: {e}")
        return []

def get_user_changelog(user_id: int, limit: int = 100) -> List[Dict]:
    """
    Get changelog entries made by a specific user
    
    Args:
        user_id: ID of the user
        limit: Maximum number of entries to return
        
    Returns:
        List of changelog entry dictionaries
    """
    try:
        with sqlite3.connect(metadata.METADATA_DB) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT cl.table_id, cl.row_pk, cl.column_name, cl.old_value, cl.new_value, 
                       cl.modified_at, tm.display_name as table_name
                FROM changelog cl
                LEFT JOIN table_meta tm ON cl.table_id = tm.id
                WHERE cl.modified_by = ?
                ORDER BY cl.modified_at DESC
                LIMIT ?
            """, (user_id, limit))
            
            entries = []
            for row in cursor.fetchall():
                entries.append({
                    'table_id': row[0],
                    'row_pk': row[1],
                    'column_name': row[2],
                    'old_value': row[3],
                    'new_value': row[4],
                    'modified_at': row[5],
                    'table_name': row[6] or 'Unknown Table'
                })
            
            return entries
    except Exception as e:
        print(f"Error getting user changelog: {e}")
        return []

def clear_changelog(table_id: int) -> bool:
    """
    Clear all changelog entries for a table (admin only)
    
    Args:
        table_id: ID of the table
        
    Returns:
        True if changelog was cleared successfully, False otherwise
    """
    try:
        # Check if user is admin
        if not app.storage.user or app.storage.user['role'] != 'admin':
            return False
        
        with sqlite3.connect(metadata.METADATA_DB) as conn:
            conn.execute("DELETE FROM changelog WHERE table_id = ?", (table_id,))
            conn.commit()
        
        return True
    except Exception as e:
        print(f"Error clearing changelog: {e}")
        return False 