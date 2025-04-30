# database.py
import sqlite3
import random

conn = None  # Global connection variable

def get_connection():
    global conn
    if conn is None:
        conn = sqlite3.connect("../DB/database.db")
    return conn

def create_database():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS Users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            first_name TEXT,
            last_name TEXT,
            email TEXT UNIQUE,
            phone TEXT
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS PurchaseHistory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            date_of_order TEXT,
            item_id INTEGER,
            amount REAL,
            seat_no INTEGER,
            token_no INTEGER,
            FOREIGN KEY (user_id) REFERENCES Users(user_id)
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS Products (
            product_id INTEGER PRIMARY KEY,
            product_name TEXT NOT NULL,
            price REAL NOT NULL
        );
        """
    )
    conn.commit()

def add_user(user_id, first_name, last_name, email, phone):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Users WHERE phone = ?", (phone,))
    if cursor.fetchone():
        return
    try:
        cursor.execute(
            """
            INSERT INTO Users (user_id, first_name, last_name, email, phone)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, first_name, last_name, email, phone),
        )
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database Error: {e}")

def get_user_by_phone(phone):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Users WHERE phone = ?", (phone,))
    return cursor.fetchone()

def get_next_user_id():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(user_id) FROM Users")
    max_id = cursor.fetchone()[0]
    if max_id is None:
        return 1
    return max_id + 1

def add_order(user_id, date_of_order, item_id, amount, seat_no, token_no):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM PurchaseHistory
        WHERE user_id = ? AND item_id = ? AND date_of_order = ?
        """,
        (user_id, item_id, date_of_order),
    )
    if cursor.fetchone():
        return
    try:
        cursor.execute(
            """
            INSERT INTO PurchaseHistory (user_id, date_of_order, item_id, amount, seat_no, token_no)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, date_of_order, item_id, amount, seat_no, token_no),
        )
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database Error: {e}")

def get_menu():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Products")
    menu = cursor.fetchall()
    return menu

def recommend_item_db(preference):
    """
    Fallback recommendation using the database (not used now).
    """
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM Products WHERE LOWER(product_name) LIKE ? LIMIT 1"
    cursor.execute(query, (f"%{preference.lower()}%",))
    item = cursor.fetchone()
    if item:
        return item
    else:
        cursor.execute("SELECT * FROM Products LIMIT 1")
        return cursor.fetchone()

def close_connection():
    global conn
    if conn:
        conn.close()
        conn = None

def preview_table(table_name):
    conn = sqlite3.connect("../DB/database.db")
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name} LIMIT 5;")
    rows = cursor.fetchall()
    for row in rows:
        print(row)
    conn.close()

def add_product(product_id, product_name, price):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Use INSERT OR IGNORE to prevent duplicate product insertion errors.
        cursor.execute(
            """
            INSERT OR IGNORE INTO Products (product_id, product_name, price)
            VALUES (?, ?, ?);
            """,
            (product_id, product_name, price),
        )
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database Error: {e}")

def initialize_database():
    global conn
    create_database()
    # Initial users
    initial_users = [
        (1, "Alice", "Smith", "alice@test.com", "123-456-7890"),
        (2, "Bob", "Johnson", "bob@test.com", "234-567-8901"),
        (3, "Sarah", "Brown", "sarah@test.com", "555-567-8901"),
    ]
    for user in initial_users:
        add_user(*user)
    # Initial orders (for testing)
    initial_orders = [
        (1, "2024-01-01 10:00:00", 1, 2.99, random.randint(1,50), random.randint(100,999)),
        (2, "2023-12-25 12:30:00", 2, 2.49, random.randint(1,50), random.randint(100,999)),
        (3, "2023-11-14 09:15:00", 3, 5.99, random.randint(1,50), random.randint(100,999)),
    ]
    for order in initial_orders:
        add_order(*order)
    # Initial products (cafe menu)
    initial_products = [
        (1, "Coffee", 2.99),
        (2, "Tea", 2.49),
        (3, "Sandwich", 5.99),
        (4, "Salad", 4.99),
        (5, "Cake", 3.99),
    ]
    for product in initial_products:
        add_product(*product)
