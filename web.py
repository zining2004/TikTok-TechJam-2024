import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_bcrypt import Bcrypt
from datetime import datetime
import requests
import random

app = Flask(__name__)
app.secret_key = os.urandom(24)
bcrypt = Bcrypt(app)

EXCHANGE_RATE_API_URL = "https://v6.exchangerate-api.com/v6/e4ac156fd352337ecfcfc3d2/latest/SGD"

# Database setup
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

connection = get_db_connection()
with connection:
    connection.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        balance REAL DEFAULT 0,
        pin INTEGER NOT NULL
    );
    ''')
    connection.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        price_per_unit REAL NOT NULL,
        image_url TEXT NOT NULL
    );
    ''')
    connection.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (product_id) REFERENCES products (id)
    );
    ''')
    connection.execute('''
    CREATE TABLE IF NOT EXISTS cart (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        image_url text not null,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (product_id) REFERENCES products (id)
    );
    ''')

    connection.execute('''
                CREATE TABLE IF NOT EXISTS exchange_rates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    currency TEXT NOT NULL UNIQUE,
                    rate REAL NOT NULL,
                    updated_at TEXT NOT NULL
                )
            ''')
    
    connection.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    type TEXT NOT NULL,
                    amount REAL NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
    
connection.close()

def fetch_and_update_exchange_rates():
    response = requests.get(EXCHANGE_RATE_API_URL)
    data = response.json()

    if response.status_code == 200 and data['result'] == 'success':
        rates = data['conversion_rates']
        updated_at = datetime.now().isoformat()

        conn = get_db_connection()
        with conn:
            for currency, rate in rates.items():
                conn.execute('''
                    INSERT INTO exchange_rates (currency, rate, updated_at)
                    VALUES (?, ?, ?)
                    ON CONFLICT(currency) DO UPDATE SET
                        rate = excluded.rate,
                        updated_at = excluded.updated_at
                ''', (currency, rate, updated_at))
        conn.close()

fetch_and_update_exchange_rates()

@app.route('/')
def index():
    conn = get_db_connection()
    featured_products = conn.execute('SELECT * FROM products WHERE id IN (5, 3, 6)').fetchall()

    if 'user_id' in session:
        user_id = session['user_id']
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        balance = user['balance'] if 'balance' in user.keys() else 0
        conn.close()
        return render_template('index.html', featured_products=featured_products, balance=balance)
    conn.close()
    return render_template('index.html', featured_products=featured_products)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        if user and bcrypt.check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials!', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirmation = request.form['confirmation']

        if password != confirmation:
            flash('Passwords do not match!', 'danger')
            return render_template('register.html')

        conn = get_db_connection()
        existing_user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()

        if existing_user:
            flash('Username already exists!', 'danger')
            conn.close()
            return render_template('register.html')

        hash = bcrypt.generate_password_hash(password).decode('utf-8')
        pin = random.randint(100000, 999999)  # Generate a 6-digit pin

        try:
            conn.execute('INSERT INTO users (username, password, pin) VALUES (?, ?, ?)', (username, hash, pin))
            conn.commit()
            flash('Registration successful!', 'success')
            return render_template('register.html', pin=pin)
        except sqlite3.IntegrityError:
            flash('An error occurred during registration. Please try again.', 'danger')
        finally:
            conn.close()

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

@app.route('/products')
def products():
    if 'user_id' not in session:
        flash('Please log in to view products.', 'danger')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products').fetchall()
    conn.close()
    return render_template('products.html', products=products)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    if 'user_id' not in session:
        flash('Please log in to add items to the cart.', 'danger')
        return redirect(url_for('login'))

    product_id = request.form['product_id']
    quantity = int(request.form['quantity'])
    user_id = session['user_id']

    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()

    if product and product['quantity'] >= quantity:
        conn.execute('INSERT INTO cart (user_id, product_id, quantity) VALUES (?, ?, ?)', (user_id, product_id, quantity))
        new_quantity = product['quantity']
        conn.execute('UPDATE products SET quantity = ? WHERE id = ?', (new_quantity, product_id))
        conn.commit()
        flash('Item added to cart!', 'success')
    else:
        flash('Not enough product in stock.', 'danger')
    
    conn.close()
    return redirect(url_for('products'))

@app.route('/cart')
def cart():
    if 'user_id' not in session:
        flash('Please log in to view your cart.', 'danger')
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db_connection()
    cart_items = conn.execute('''
        SELECT cart.id, products.name, products.image_url, cart.quantity, products.price_per_unit, products.quantity AS stock
        FROM cart
        JOIN products ON cart.product_id = products.id
        WHERE cart.user_id = ?
    ''', (user_id,)).fetchall()

    total_amount = sum(item['quantity'] * item['price_per_unit'] for item in cart_items)

    conn.close()
    return render_template('cart.html', cart_items=cart_items, total_amount=total_amount)

@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    if 'user_id' not in session:
        flash('Please log in to modify your cart.', 'danger')
        return redirect(url_for('login'))

    cart_id = request.form['cart_id']
    user_id = session['user_id']

    conn = get_db_connection()
    conn.execute('DELETE FROM cart WHERE id = ? AND user_id = ?', (cart_id, user_id))
    conn.commit()
    conn.close()
    flash('Item removed from cart!', 'success')
    return redirect(url_for('cart'))

@app.route('/purchase_cart', methods=['POST'])
def purchase_cart():
    if 'user_id' not in session:
        flash('Please log in to purchase items.', 'danger')
        return redirect(url_for('login'))

    user_id = session['user_id']
    total_amount = float(request.form['total_amount'])
    pin = int(request.form['pin'])

    conn = get_db_connection()
    user = conn.execute('SELECT balance, pin FROM users WHERE id = ?', (user_id,)).fetchone()

    if user['pin'] != pin:
        flash('Invalid PIN.', 'danger')
        conn.close()
        return redirect(url_for('cart'))

    if user['balance'] < total_amount:
        flash('Insufficient balance to complete the purchase.', 'danger')
        conn.close()
        return redirect(url_for('cart'))

    cart_items = conn.execute('SELECT * FROM cart WHERE user_id = ?', (user_id,)).fetchall()

    for item in cart_items:
        product = conn.execute('SELECT * FROM products WHERE id = ?', (item['product_id'],)).fetchone()
        new_quantity = product['quantity'] - item['quantity']
        conn.execute('UPDATE products SET quantity = ? WHERE id = ?', (new_quantity, product['id']))
        conn.execute('INSERT INTO orders (user_id, product_id, quantity) VALUES (?, ?, ?)', (user_id, item['product_id'], item['quantity']))

    conn.execute('UPDATE users SET balance = balance - ? WHERE id = ?', (total_amount, user_id))
    conn.execute('DELETE FROM cart WHERE user_id = ?', (user_id,))
    conn.execute('INSERT INTO transactions (user_id, type, amount) VALUES (?, ?, ?)', (user_id, 'Purchase', total_amount))
    conn.commit()
    conn.close()

    flash('Purchase successful!', 'success')
    return redirect(url_for('products'))


@app.route('/topup', methods=['GET', 'POST'])
def topup():
    if 'user_id' not in session:
        flash('Please log in to top-up your account.', 'danger')
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db_connection()
    
    if request.method == 'POST':
        payment_method = request.form['payment_method']
        currency = request.form['currency']
        amount = float(request.form['amount'])
        exchange_rate = conn.execute('SELECT rate FROM exchange_rates WHERE currency = ?', (currency,)).fetchone()['rate']
        tiktoken_amount = amount / exchange_rate

        if payment_method == 'credit_card':
            card_number = request.form['card_number']
            expiry_date = request.form['expiry_date']
            cvv = request.form['cvv']
            # Assume the credit card is processed here
            
            user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
            new_balance = user['balance'] + tiktoken_amount
            conn.execute('UPDATE users SET balance = ? WHERE id = ?', (new_balance, user_id))
            conn.execute('INSERT INTO transactions (user_id, type, amount) VALUES (?, ?, ?)', (user_id, 'Top-Up', tiktoken_amount))
            conn.commit()
            flash('Top-up successful!', 'success')
    
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    balance = user['balance']
    conn.close()

    return render_template('topup.html', balance=round(balance, 2))

@app.route('/orders')
def orders():
    if 'user_id' not in session:
        flash('Please log in to view your orders.', 'danger')
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db_connection()
    orders = conn.execute('''
        SELECT orders.id, products.name, orders.quantity
        FROM orders
        JOIN products ON orders.product_id = products.id
        WHERE orders.user_id = ?
    ''', (user_id,)).fetchall()
    conn.close()
    return render_template('orders.html', orders=orders)

@app.route('/transfer', methods=['GET', 'POST'])
def transfer():
    if 'user_id' not in session:
        flash('Please log in to transfer TikTokens.', 'danger')
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db_connection()
    user = conn.execute('SELECT balance, pin FROM users WHERE id = ?', (user_id,)).fetchone()

    if request.method == 'POST':
        recipient_username = request.form['recipient_username']
        transfer_amount = float(request.form['transfer_amount'])
        pin = int(request.form['pin'])

        if user['pin'] != pin:
            flash('Invalid PIN.', 'danger')
            return render_template('transfer.html', balance=user['balance'])

        recipient = conn.execute('SELECT * FROM users WHERE username = ?', (recipient_username,)).fetchone()

        if not recipient:
            flash('Recipient username does not exist.', 'danger')
        elif user['balance'] < transfer_amount:
            flash('Insufficient balance to complete the transfer.', 'danger')
        else:
            conn.execute('UPDATE users SET balance = balance - ? WHERE id = ?', (transfer_amount, user_id))
            conn.execute('UPDATE users SET balance = balance + ? WHERE id = ?', (transfer_amount, recipient['id']))
            conn.execute('INSERT INTO transactions (user_id, type, amount) VALUES (?, ?, ?)', (user_id, 'Transfer Out', transfer_amount))
            conn.execute('INSERT INTO transactions (user_id, type, amount) VALUES (?, ?, ?)', (recipient['id'], 'Transfer In', transfer_amount))
            conn.commit()
            flash('Transfer successful!', 'success')

    conn.close()
    return render_template('transfer.html', balance=user['balance'])

@app.route('/transactions')
def transactions():
    if 'user_id' not in session:
        flash('Please log in to view your transactions.', 'danger')
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db_connection()
    transactions = conn.execute('SELECT * FROM transactions WHERE user_id = ?', (user_id,)).fetchall()
    conn.close()

    return render_template('transactions.html', transactions=transactions)

@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f'Unhandled exception: {request.url} - {e}')
    return render_template('error.html'), 500

if __name__ == '__main__':
    app.run(debug=True)
