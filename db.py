import sqlite3

def create_tables():
    conn = sqlite3.connect('marketplace.db')
    c = conn.cursor()
    
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        rowid INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        email TEXT,
        balance REAL
    )
    ''')
    
    c.execute('''
    CREATE TABLE IF NOT EXISTS items (
        rowid INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        price REAL,
        quantity INTEGER,
        description TEXT,
        image TEXT,
        user_id INTEGER,
        FOREIGN KEY(user_id) REFERENCES users(rowid)
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        rowid INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id INTEGER,
        user_id INTEGER,
        seller_id INTEGER,
        quantity INTEGER,
        price REAL,
        description TEXT,
        image TEXT,
        name TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(item_id) REFERENCES items(rowid),
        FOREIGN KEY(user_id) REFERENCES users(rowid)
    )
    ''')
    
    conn.commit()
    conn.close()



