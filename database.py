import sqlite3
import hashlib
import pandas as pd

DB_NAME = "retail_saas.db"

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, role TEXT NOT NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS transactions (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp DATETIME, cashier_id TEXT NOT NULL, item_category TEXT NOT NULL, cart_value REAL NOT NULL, discount REAL NOT NULL, voided_items INTEGER NOT NULL, anomaly_flag INTEGER DEFAULT 0, status TEXT DEFAULT 'Pending_Review')''')
    
    cursor.execute("SELECT * FROM users WHERE username='admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", ("admin", hash_password("admin123"), "Admin"))
        
    cursor.execute("SELECT * FROM users WHERE username='C01'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", ("C01", hash_password("pass123"), "Employee"))
    conn.commit()
    conn.close()

def verify_login(username, password):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM users WHERE username=? AND password_hash=?", (username, hash_password(password)))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

# === USER MANAGEMENT CRUD FUNCTIONS ===
def add_user(username, password, role="Employee"):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", (username, hash_password(password), role))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False 
    conn.close()
    return success

def get_all_employees():
    """Fetches all users who are not Admins."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users WHERE role = 'Employee'")
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return users

def delete_user(username):
    """Revokes access by deleting the employee."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE username=?", (username,))
    conn.commit()
    conn.close()

def reset_password(username, new_password):
    """Updates an employee's password hash."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET password_hash=? WHERE username=?", (hash_password(new_password), username))
    conn.commit()
    conn.close()

# === TRANSACTION FUNCTIONS ===
def log_transaction(tx_timestamp, cashier_id, category, value, discount, voids, anomaly_flag, status):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO transactions (timestamp, cashier_id, item_category, cart_value, discount, voided_items, anomaly_flag, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (tx_timestamp, cashier_id, category, value, discount, voids, anomaly_flag, status))
    tx_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return tx_id

def get_transaction_status(tx_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM transactions WHERE id = ?", (tx_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def bootstrap_db_from_csv(uploaded_file):
    df = pd.read_csv(uploaded_file)
    df.columns = df.columns.str.strip().str.lower()
    column_mapping = {'discount_percent': 'discount', 'cashier': 'cashier_id', 'category': 'item_category', 'cartvalue': 'cart_value', 'voids': 'voided_items'}
    df.rename(columns=column_mapping, inplace=True)
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    for index, row in df.iterrows():
        cursor.execute('''
            INSERT INTO transactions (timestamp, cashier_id, item_category, cart_value, discount, voided_items, anomaly_flag, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (row.get('timestamp', None), row.get('cashier_id', 'UNKNOWN'), row.get('item_category', 'UNKNOWN'), row.get('cart_value', 0.0), row.get('discount', 0.0), row.get('voided_items', 0), row.get('anomaly_flag', 0), row.get('status', 'Approved')))
    conn.commit()
    conn.close()
    return len(df)

if __name__ == "__main__":
    init_db()