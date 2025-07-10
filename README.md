# Directory structure layout

```
layout.html
utils.py
config copy.py
nococlone.db
.cursorignore
sample_data.db
layout
layout/main_layout.py
layout/layout.py
pages
pages/register.py
pages/admin_users_page.py
pages/logout.py
pages/admin_invite_page.py
pages/grid_demo.py
pages/permissions_page.py
pages/login.py
pages/table_view.py
pages/home.py
main.py
metadata.py
archive
README.md
layout_template.py
requirements.txt
help
help/ui.txt
help/ui.input
nocoflo.db
explore
explore/app.py
config.py
plan
plan/plan.md
components
components/README.md
components/grid.p
```

# NocoClone MVP

A NocoDB-like application built with NiceGUI that allows you to create spreadsheet-like interfaces for any SQL database.

## Features

✅ **Multi-Database Support** - Connect to different SQL databases  
✅ **User Authentication** - Login/logout with bcrypt password hashing  
✅ **Role-Based Access Control** - Admin, Owner, and User roles  
✅ **Table Permissions** - Read, Write, Delete, and Owner permissions per table  
✅ **Real-time Collaboration** - Row-level locking and live updates  
✅ **Audit Logging** - Track all changes with user, timestamp, and old/new values  
✅ **Invite System** - Admins can invite new users via email tokens  
✅ **Sidebar Navigation** - NocoDB-style database and table browser  
✅ **Inline Editing** - Edit cells directly in the grid interface  
✅ **Change History** - View and filter audit logs per table  

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Application
```bash
python main.py
```

### 3. Access the Application
Open your browser to `http://localhost:8082`

### 4. Default Admin Login
- **Email:** `admin@nococlone.com`
- **Password:** `admin123`

## Usage

### Admin Functions
- **User Management** (`/admin/users`): View, promote/demote, and delete users
- **Invite Users** (`/admin/invite`): Generate invite links for new users
- **Full Access**: Admins can view and edit all tables

### User Registration
1. Admin creates an invite link
2. New user clicks the invite link
3. User fills out registration form
4. Admin assigns table permissions

### Database Setup
The application uses two types of databases:

1. **Metadata Database** (`nococlone.db`): Stores users, permissions, table metadata, etc.
2. **Data Databases**: Your actual data tables (can be SQLite, PostgreSQL, MySQL, etc.)

### Sample Data
The application creates a sample database (`sample_data.db`) with a `users` table for testing.

## Architecture

### Key Tables (in nococlone.db)
- `user` - User accounts and roles
- `dbconfig` - Database connection configurations  
- `table_meta` - Table metadata and display names
- `permission` - User permissions per table
- `changelog` - Audit log of all changes
- `row_lock` - Real-time collaboration locks
- `invite` - Invite tokens for new users

### Permission Levels
- **Read**: View table data
- **Write**: Edit existing rows and add new rows
- **Delete**: Delete rows
- **Owner**: Full control + manage permissions

### Real-time Features
- Row-level locking prevents edit conflicts
- Automatic table refresh when others make changes
- Live audit log updates

## Security Features

- Bcrypt password hashing
- Session-based authentication
- Permission checks on all operations
- SQL injection prevention via parameterized queries

## Extending the Application

### Adding New Database Types
Update the `con_str` format in `dbconfig` table and modify `get_table_data()` function.

### Custom UI Themes
Modify the `.classes()` calls throughout the code to use different Tailwind CSS classes.

### Additional Permissions
Extend the `permission` table and update `has_permission()` function.

## Troubleshooting

### Navigation Issues
If you get `AttributeError: module 'nicegui.ui' has no attribute 'navigate'`, make sure you're using the correct NiceGUI version (1.4.0+) and that the navigation is handled via `ui.run_javascript('window.location.href = "/path"')`.

### Database Connection Errors
- Ensure your database connection strings in `dbconfig` are valid
- Check that external databases are accessible
- Verify SQLAlchemy drivers are installed for your database type

### Permission Denied
- Check that users have the correct permissions in the `permission` table
- Verify the user's role in the `user` table
- Admins always have full access regardless of explicit permissions

## License

MIT License - feel free to modify and use for your projects! 