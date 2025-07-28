import sqlite3
from nicegui import app
from typing import Dict, List, Optional

import metadata

def has_permission(table_id: int, permission: str) -> bool:
    """
    Check if current user has specific permission on a table
    
    Args:
        table_id: ID of the table to check
        permission: Permission to check ('read', 'write', 'delete', 'owner')
        
    Returns:
        True if user has permission, False otherwise
    """
    return metadata.has_permission(table_id, permission)

def get_user_permissions(table_id: int, user_id: int) -> Dict[str, bool]:
    """
    Get all permissions for a specific user on a table
    
    Args:
        table_id: ID of the table
        user_id: ID of the user
        
    Returns:
        Dictionary with permission flags
    """
    with sqlite3.connect(metadata.METADATA_DB) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT can_read, can_write, can_delete, is_owner
            FROM permission 
            WHERE user_id = ? AND table_id = ?
        """, (user_id, table_id))
        
        row = cursor.fetchone()
        if not row:
            return {
                'can_read': False,
                'can_write': False,
                'can_delete': False,
                'is_owner': False
            }
        
        return {
            'can_read': bool(row[0]),
            'can_write': bool(row[1]),
            'can_delete': bool(row[2]),
            'is_owner': bool(row[3])
        }

def grant_permission(table_id: int, user_id: int, permission_level: str) -> bool:
    """
    Grant permission to a user on a table
    
    Args:
        table_id: ID of the table
        user_id: ID of the user
        permission_level: Permission level ('read', 'write', 'delete', 'owner')
        
    Returns:
        True if permission was granted successfully, False otherwise
    """
    try:
        # Set permission flags based on level
        can_read = 1
        can_write = 1 if permission_level in ['write', 'delete', 'owner'] else 0
        can_delete = 1 if permission_level in ['delete', 'owner'] else 0
        is_owner = 1 if permission_level == 'owner' else 0
        
        with sqlite3.connect(metadata.METADATA_DB) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO permission 
                (user_id, table_id, can_read, can_write, can_delete, is_owner)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, table_id, can_read, can_write, can_delete, is_owner))
            conn.commit()
        
        return True
    except Exception as e:
        print(f"Error granting permission: {e}")
        return False

def revoke_permission(table_id: int, user_id: int) -> bool:
    """
    Revoke all permissions for a user on a table
    
    Args:
        table_id: ID of the table
        user_id: ID of the user
        
    Returns:
        True if permission was revoked successfully, False otherwise
    """
    try:
        with sqlite3.connect(metadata.METADATA_DB) as conn:
            conn.execute("""
                DELETE FROM permission 
                WHERE user_id = ? AND table_id = ?
            """, (user_id, table_id))
            conn.commit()
        
        return True
    except Exception as e:
        print(f"Error revoking permission: {e}")
        return False

def get_table_users(table_id: int) -> List[Dict]:
    """
    Get all users and their permissions for a table
    
    Args:
        table_id: ID of the table
        
    Returns:
        List of user dictionaries with permission information
    """
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
        
        users = []
        for row in cursor.fetchall():
            users.append({
                'id': row[0],
                'name': row[1],
                'email': row[2],
                'role': row[3],
                'can_read': bool(row[4]),
                'can_write': bool(row[5]),
                'can_delete': bool(row[6]),
                'is_owner': bool(row[7])
            })
        
        return users

def can_manage_permissions(table_id: int) -> bool:
    """
    Check if current user can manage permissions for a table
    
    Args:
        table_id: ID of the table
        
    Returns:
        True if user can manage permissions, False otherwise
    """
    if not app.storage.user:
        return False
    
    # Admins can manage all permissions
    if app.storage.user['role'] == 'admin':
        return True
    
    # Table owners can manage permissions
    return has_permission(table_id, 'owner')

def get_permission_level_name(permissions: Dict[str, bool]) -> str:
    """
    Get human-readable permission level name
    
    Args:
        permissions: Dictionary with permission flags
        
    Returns:
        Human-readable permission level
    """
    if permissions.get('is_owner'):
        return 'Owner'
    elif permissions.get('can_delete'):
        return 'Delete'
    elif permissions.get('can_write'):
        return 'Write'
    elif permissions.get('can_read'):
        return 'Read'
    else:
        return 'None' 