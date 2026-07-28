import sqlite3

def migrate():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    # Check columns in items table
    cursor.execute("PRAGMA table_info(items)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if "category" not in columns:
        cursor.execute("ALTER TABLE items ADD COLUMN category VARCHAR DEFAULT 'consumable'")
        print("Added column category to items")
        
    if "min_stock_alert" not in columns:
        cursor.execute("ALTER TABLE items ADD COLUMN min_stock_alert INTEGER DEFAULT 5")
        print("Added column min_stock_alert to items")
        
    if "location" not in columns:
        cursor.execute("ALTER TABLE items ADD COLUMN location VARCHAR DEFAULT 'Kho Kỹ Thuật'")
        print("Added column location to items")

    # Check columns in users table
    cursor.execute("PRAGMA table_info(users)")
    u_columns = [col[1] for col in cursor.fetchall()]

    if "hashed_password" not in u_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN hashed_password VARCHAR")
        print("Added column hashed_password to users")

    if "full_name" not in u_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN full_name VARCHAR")
        print("Added column full_name to users")

    if "department" not in u_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN department VARCHAR")
        print("Added column department to users")

    conn.commit()
    conn.close()
    print("Database migration completed successfully!")

if __name__ == "__main__":
    migrate()
