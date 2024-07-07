# TikTok TechJam 2024

### Team Name: ScratchTheCat

## Problem Statement
Reshaping Payments - Wallets

## TikToken

### Overview
This project is an e-commerce platform built with Flask, a lightweight web application framework in Python. The platform allows users to browse products, add items to a shopping cart, top up their account balance, transfer their balances, and make purchases. The platform supports both cash and credit card top-ups, with exchange rates dynamically fetched from an API.

### Features
- User Authentication: Users can register, log in, and log out.
- Product Browsing: Users can browse featured products and view details such as name, price, and available quantity.
- Shopping Cart: Users can add items to a shopping cart and view the total amount.
- Top-Up Balance: Users can top up their account balance using cash or credit card. The balance is displayed in TikToken, with exchange rates fetched from an API.
- Order History: Users can view their past orders.
- Transfer: Users can transfer TikTokens to existing users. 
- Transaction History: Users can view their history of purchases, top-ups, and transfers.
- Security Feature: A 6-digit pin given upon registration is required for purchases and transfers.
- Error Handling: Users will not be able to see the backend error message if an error is faced. 

### Prerequisites
Python 3.7 or higher
SQLite

### Project Structure
- web.py: Main application file containing routes and logic.
- templates/: Directory containing HTML templates.
- index.html: Home page template.
- login.html: Login page template.
- register.html: Registration page template.
- products.html: Product browsing template.
- cart.html: Shopping cart template.
- topup.html: Top-up balance template.
- transfer.html: Transfer TikTokens template.
- error.html: Error template.
- layout.html: template.
- orders.html: Orders template.
- transactions.html: Transaction history template.
- static/: Directory containing static files (CSS, images).
- style.css: Main stylesheet.
- database.db: contain examples of products, carts, users, orders, and exchange rates. 

### Usage
- User Registration:
Navigate to the registration page and create a new account by providing a username and password and will receive a 6-digit pin. 
- User Login:
Log in to your account using your registered username and password.
- Browsing Products:
Browse the available products on the home page or the products page. You can view product details, including price and quantity.
- Shopping Cart:
Add products to your cart and view the total amount. Remove items from the cart if needed. Will require the 6-digit pin to purchase. 
- Top-Up Balance:
Top up your account balance using cash or a credit card. For credit card top-ups, select the currency and enter your card details. The amount will be converted to TikTokens based on the current exchange rate.
- Viewing Orders:
View your past orders and purchase history.
- Transferring of TikTokens: 
Allow users to transfer TikTokens to other existing users and will require the 6-digit pin. 
- Transaction History:
Allow users to track their top-ups, transfers, and purchase history.

## Kiosk
This is a prototype (Flask-based web application) for a Kiosk Machine that allows users to log in and top up their balances in TikToken using various currencies. The application fetches real-time exchange rates using an external API.

### Features
- User Login
- Balance Top-Up
- Real-time Currency Conversion using ExchangeRate-API

### Prerequisites
- Python 3.10+
- Flask
- SQLite
- requests

### Project Structure
- app.py: Main application file containing routes and logic.
- templates/: Directory containing HTML templates.
- index.html: Home page template.
- topup.html: Top-up balance template.
- static/: Directory containing static files (CSS).
- style.css: Main stylesheet.

## Future Improvements
- Implement more robust error handling and validation.
- Enhance the admin interface for better product management.
- Add support for more payment methods.
- Improve UI/UX design.

## Acknowledgments
- Flask: https://flask.palletsprojects.com/
- SQLite: https://www.sqlite.org/
- Exchange Rate API: https://www.exchangerate-api.com/
