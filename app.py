from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from db import create_tables
import sqlite3
import json
import plotly.express as px

app = Flask(__name__)
app.secret_key = 'supersecretkey'

def get_db_connection():
    conn = sqlite3.connect('marketplace.db')
    conn.row_factory = sqlite3.Row
    return conn


def debag(query):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(query)
    items = c.fetchall()
    conn.close()
    print(query , " : Query")
    print(items)


@app.route('/')
def index():
    balance = 'NaN'
    username = 'NaN'
    items = []
    offers = []
    if 'user_id' in session:
        user_id = session['user_id']
        balance = get_user_balance(session['user_id'])
        username = get_username(session['user_id'])
        items = get_user_items(session['user_id'])
        offers = get_user_offers(session['user_id'])
    return render_template('index.html', balance=balance , username=username , items=items , offers=offers , user_id=user_id)

def get_username(user_id):
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT username FROM users WHERE rowid = ?', (user_id,))
        username = c.fetchone()['username']
        conn.close()
        return username
    except:
        return 'NaN'
    
def get_email(user_id):
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT email FROM users WHERE rowid = ?', (user_id,))
        email = c.fetchone()['email']
        conn.close()
        return email
    except:
        return 'NaN'

@app.route('/get_historical_price_for_item/<int:item_id>')
def get_historical_price_for_item(item_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM orders WHERE item_id = ? ORDER BY timestamp DESC', (item_id,))
    prices = c.fetchall()
    conn.close()
    return render_template('historical_prices.html', prices=prices)

@app.route('/buy_item/<int:item_id>', methods=['POST'])
def buy_item(item_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    c = conn.cursor()

    # Get item details
    c.execute('SELECT * FROM items WHERE rowid = ?', (item_id,))
    item = c.fetchone()
    
    # Get user details
    c.execute('SELECT * FROM users WHERE rowid = ?', (session['user_id'],))
    user = c.fetchone()

    if item and user:
        if item['quantity'] > 0 and user['balance'] >= item['price']:
            new_balance = user['balance'] - item['price']
            new_quantity = item['quantity'] - 1

            # Update user's balance
            c.execute('UPDATE users SET balance = ? WHERE rowid = ?', (new_balance, session['user_id']))

            # Update item's quantity
            c.execute('UPDATE items SET quantity = ? WHERE rowid = ?', (new_quantity, item_id))

            # Add order
            # get seller_id
            c.execute('SELECT user_id FROM items WHERE rowid = ?', (item_id,))
            seller_id = c.fetchone()['user_id']

            c.execute('INSERT INTO orders (item_id, user_id, seller_id ,  quantity , price , description , image , name, category) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', (item_id, session['user_id'], seller_id, 1, item['price'], item['description'], item['image'], item['name'], item['category']))

            conn.commit()
            flash('Purchase successful!')
        else:
            flash('Insufficient balance or item out of stock.')
    conn.close()
    return redirect(url_for('list_items'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        balance = float(request.form['balance'])

        conn = get_db_connection()
        c = conn.cursor()
        hashed_password = generate_password_hash(password)
        try:
            c.execute('INSERT INTO users (username, password, email, balance) VALUES (?, ?, ?, ?)',
                      (username, hashed_password, email, balance))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return 'Username already taken'
        conn.close()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = c.fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['rowid']
            return redirect(url_for('index'))
        return 'Invalid credentials'
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

@app.route('/add_item', methods=['GET', 'POST'])
def add_item():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        price = float(request.form['price'])
        quantity = int(request.form['quantity'])
        description = request.form['description']
        image = request.form['image']
        category = request.form['category']
        
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('INSERT INTO items (name, price, quantity, description, image, user_id, category) VALUES (?, ?, ?, ?, ?, ?, ?)',
                  (name, price, quantity, description, image, session['user_id'], category) )
        conn.commit()
        conn.close()
        
        return redirect(url_for('list_items'))
    
    return render_template('add_item.html')

def update_user_profile(user_id, new_username, new_password, new_email):
    conn = get_db_connection()
    c = conn.cursor()
    hashed_password = generate_password_hash(new_password)
    c.execute('UPDATE users SET username = ?, password = ?, email = ? WHERE rowid = ?', (new_username, hashed_password, new_email, user_id))
    conn.commit()
    conn.close()

@app.route('/profile/<int:user_id>', methods=['GET', 'POST'])
def profile(user_id):
    username = get_username(user_id)
    email = get_email(user_id)  # Assuming you have a function to retrieve the user's email
    if request.method == 'POST':
        new_username = request.form['username']
        new_password = request.form['password']
        new_email = request.form['email']
        update_user_profile(user_id, new_username, new_password, new_email)
        return redirect(url_for('index', user_id=user_id))
    return render_template('profile.html', user_id=user_id, username=username, email=email)

def get_spending(user_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM orders WHERE user_id = ?', (user_id,))
    orders = c.fetchall()
    conn.close()

    timestamps = []
    cumulative_spending = []
    total_spending = 0

    for order in orders:
        total_spending += order['price']
        timestamps.append(order['timestamp'])
        cumulative_spending.append(total_spending)
    
    if not orders:
        return [], 0, None

    print(timestamps)
    print(cumulative_spending)

    fig = px.line(x=timestamps, y=cumulative_spending, labels={'x': 'Timestamp', 'y': 'Cumulative Spending'})
    graph = fig.to_html(full_html=False)

    return orders, total_spending, graph

@app.route('/balance/<int:user_id>')
def balance(user_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if not user_id:
        return "User ID is required"
    orders, total_spending, graph = get_spending(user_id)
    return render_template('balance.html', orders=orders, Total_spading=total_spending, graph=graph)

@app.route('/show_all_orders')
def show_all_orders():
    conn = get_db_connection()
    c = conn.cursor()

    search_query = request.args.get('search_query')
    if search_query:
        c.execute("""
        SELECT *
        FROM orders
        WHERE name LIKE ? OR description LIKE ?
        """, ('%' + search_query + '%', '%' + search_query + '%'))
    else:
        c.execute("""
        SELECT * FROM orders 
        """)

    # debag("""
    # SELECT orders.*, 
    #        seller.username AS seller_name, 
    #        buyer.username AS buyer_name
    # FROM orders
    # LEFT JOIN users AS seller ON orders.seller_id = user_id
    # LEFT JOIN users AS buyer ON orders.user_id = user_id
    # """)

    orders = c.fetchall()
    orders_temp = []
    for order in orders:
        order_temp = dict(order)
        order_temp['seller_name'] = get_username(order['seller_id'])
        order_temp['buyer_name'] = get_username(order['user_id'])
        orders_temp.append(order_temp)

    conn.close()
    return render_template('show_all_orders.html', orders=orders_temp)

@app.route('/show_all_orders_rerender')
def show_all_orders_rerender():
    return redirect(url_for('show_all_orders'))

@app.route('/list_items')
def list_items():
    search_query = request.args.get('search_query')
    conn = get_db_connection()
    c = conn.cursor()
    
    if search_query:
        c.execute('SELECT * FROM items WHERE (name LIKE ? OR description LIKE ?) AND quantity > 0', 
                  ('%' + search_query + '%', '%' + search_query + '%'))
    else:
        c.execute('SELECT * FROM items WHERE quantity > 0')
        
    items = c.fetchall()
    conn.close()
    
    return render_template('list_items.html', items=items)

@app.route('/edit_item/<int:item_id>', methods=['GET', 'POST'])
def edit_item(item_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    c = conn.cursor()
    
    if request.method == 'POST':
        name = request.form['name']
        price = float(request.form['price'])
        quantity = int(request.form['quantity'])
        description = request.form['description']
        image = request.form['image']

        c.execute('UPDATE items SET name = ?, price = ?, quantity = ?, description = ?, image = ? WHERE rowid = ? AND user_id = ?',
                    (name, price, quantity, description, image, item_id, session['user_id']))
        conn.commit()
        conn.close()
        
        return redirect(url_for('index'))

    # Code to retrieve and display item details

    c.execute('SELECT * FROM items WHERE rowid = ? AND user_id = ?', (item_id, session['user_id']))
    item = c.fetchone()
    conn.close()

    if item is None:
        return 'Item not found or you do not have permission to edit this item.'

    return render_template('edit_item.html', item=item)


def get_user_balance(user_id):
    try :
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT balance FROM users WHERE rowid = ?', (user_id,))
        balance = c.fetchone()['balance']
        conn.close()
        return balance
    except:
        return "NaN"
    

def get_user_items(user_id , search_query = None):
    conn = get_db_connection()
    c = conn.cursor()
    if search_query:
        c.execute('SELECT * FROM orders WHERE user_id = ? AND (name LIKE ? OR description LIKE ?)', (user_id, '%' + search_query + '%', '%' + search_query + '%'))
    else:
        c.execute('SELECT * FROM orders WHERE user_id = ?', (user_id,))
    items = c.fetchall()
    print(len(items))
    conn.close()
    return items

def get_user_offers(user_id , search_query = None):
    print("search_query",search_query)
    print("user_id",user_id)
    conn = get_db_connection()
    c = conn.cursor()
    if search_query:
        c.execute('SELECT * FROM items WHERE user_id = ? AND (name LIKE ? OR description LIKE ?)', (user_id, '%' + search_query + '%', '%' + search_query + '%'))
    else:
        c.execute('SELECT * FROM items WHERE user_id = ?', (user_id,))
    items = c.fetchall()
    print(len(items))
    conn.close()
    return items

@app.route('/search_offers', methods=['GET', 'POST'])
def search_offers():
    search_query = request.args.get('search_query')

    balance = 'NaN'
    username = 'NaN'
    items = []
    offers = []
    if 'user_id' in session:
        balance = get_user_balance(session['user_id'])
        username = get_username(session['user_id'])
        if search_query:
            offers = get_user_offers(session['user_id'], search_query)
            if not offers:
                flash('No offers found')
                offers = get_user_offers(session['user_id'])
        else:
            offers = get_user_offers(session['user_id'])
        items = get_user_items(session['user_id'])

    return render_template('index.html', balance=balance, username=username, items=items, offers=offers)


@app.route('/search_bought_items', methods=['GET', 'POST'])
def search_bought_items():
    search_query = request.args.get('search_query')
    balance = 'NaN'
    username = 'NaN'
    items = []
    offers = []
    if 'user_id' in session:
        balance = get_user_balance(session['user_id'])
        username = get_username(session['user_id'])
        if search_query:
            items = get_user_items(session['user_id'], search_query)
            if not items:
                flash('No items found')
                items = get_user_items(session['user_id'])
        else:
            items = get_user_items(session['user_id'])
        offers = get_user_offers(session['user_id'])

    return render_template('index.html', balance=balance, username=username, items=items, offers=offers)

@app.route('/reset_search' , methods=['GET' , 'POST'])
def reset_search():
    return redirect(url_for('index'))

@app.route('/reset_search_offers' , methods=['GET' , 'POST'])
def reset_search_offers():
    return redirect(url_for('list_items'))


if __name__ == '__main__':
    create_tables()
    app.run(debug=True)
