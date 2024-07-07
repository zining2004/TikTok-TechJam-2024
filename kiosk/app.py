from flask import Flask, render_template, request, redirect, url_for, session
import os
import sqlite3
import requests

app = Flask(__name__)
app.secret_key = os.urandom(24)

def get_db_connection():
    conn = sqlite3.connect('kiosk_database.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_exchange_rates():
    api_key = 'YOUR_API_KEY'  
    url = f'https://v6.exchangerate-api.com/v6/e4ac156fd352337ecfcfc3d2/latest/SGD'
    try:
        response = requests.get(url)
        response.raise_for_status() 
        data = response.json()
        return data['conversion_rates']
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.RequestException) as e:
        print(f"Error fetching exchange rates: {e}")
        return {
            "USD": 0.75,
            "SGD": 1.0,
            "EUR": 0.65,
        }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
    conn.close()
    
    if user:
        user_id = user['id']
        session['user_id'] = user_id
        return redirect(url_for('topup', user_id=user_id))
    else:
        return redirect(url_for('index'))

@app.route('/topup', methods=['GET', 'POST'])
def topup():
    if 'user_id' not in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        amount = float(request.form['amount'])
        currency = request.form['currency']
        user_id = session['user_id']

        exchange_rates = get_exchange_rates()
        
        if currency in exchange_rates:
            amount_in_sgd = amount * exchange_rates['SGD'] / exchange_rates[currency]
        else:
            amount_in_sgd = amount 

        conn = get_db_connection()
        conn.execute('UPDATE users SET balance = balance + ? WHERE id = ?', (amount_in_sgd, user_id))
        conn.commit()
        conn.close()

        return redirect(url_for('topup'))

    user_id = session['user_id']
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    balance = user['balance']
    exchange_data = get_exchange_rates()

    return render_template('topup.html', balance=balance, exchange_data=exchange_data, user_id=user_id)

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
