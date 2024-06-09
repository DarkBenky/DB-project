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
        category TEXT,
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
        category TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(item_id) REFERENCES items(rowid),
        FOREIGN KEY(user_id) REFERENCES users(rowid)
    )
    ''')

    # check if the table are empty
    results = c.execute('SELECT * FROM users')
    if not results.fetchall():
        populate()
    
    conn.commit()
    conn.close()


def populate():
    conn = sqlite3.connect('marketplace.db')
    c = conn.cursor()
    
    # Insert users
    users = [
        ('alice', 'password123', 'alice@example.com', 100.00),
        ('bob', 'securepassword', 'bob@example.com', 150.50),
        ('charlie', 'mypassword', 'charlie@example.com', 200.75)
    ]
    c.executemany('INSERT INTO users (username, password, email, balance) VALUES (?, ?, ?, ?)', users)
    
    # Insert items
    items = [
        ('Laptop', 999.99, 10, 'A high-performance laptop.', 'https://picsum.photos/200?category=electronics', 1, 'Electronics'),
        ('Smartphone', 499.99, 25, 'Latest model smartphone.', 'https://picsum.photos/200?category=electronics', 2, 'Electronics'),
        ('Headphones', 199.99, 50, 'Noise-cancelling headphones.', 'https://picsum.photos/200?category=electronics', 3, 'Electronics'),
        ('Coffee Maker', 89.99, 15, 'Brews great coffee.', 'https://picsum.photos/200?category=home', 1, 'Home Appliances'),
        ('Book: Python Programming', 29.99, 100, 'Learn Python programming.', 'https://picsum.photos/200?category=books', 2, 'Books')
    ]
    c.executemany('INSERT INTO items (name, price, quantity, description, image, user_id, category) VALUES (?, ?, ?, ?, ?, ?, ?)', items)
    
    # Insert orders
    orders = [
        (1, 3, 1, 1, 999.99, 'A high-performance laptop.', 'https://picsum.photos/200?category=electronics', 'Laptop', 'Electronics'),
        (2, 1, 2, 2, 499.99, 'Latest model smartphone.', 'https://picsum.photos/200?category=electronics', 'Smartphone', 'Electronics'),
        (3, 2, 3, 2, 199.99, 'Noise-cancelling headphones.', 'https://picsum.photos/200?category=electronics', 'Headphones', 'Electronics'),
        (4, 3, 2, 1, 89.99, 'Brews great coffee.', 'https://picsum.photos/200?category=home', 'Coffee Maker', 'Home Appliances')
    ]
    c.executemany('INSERT INTO orders (item_id, user_id, seller_id, quantity, price, description, image, name, category) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', orders)
    
    conn.commit()
    conn.close()