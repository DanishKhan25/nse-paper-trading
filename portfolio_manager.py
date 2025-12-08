import sqlite3
import pandas as pd
from datetime import datetime
import streamlit as st

class PortfolioManager:
    def __init__(self, db_path="trading.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create holdings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS holdings (
                symbol TEXT PRIMARY KEY,
                quantity INTEGER NOT NULL,
                avg_price REAL NOT NULL
            )
        ''')
        
        # Create orders table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                order_type TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                timestamp TEXT NOT NULL,
                status TEXT NOT NULL,
                strategy TEXT
            )
        ''')
        
        # Create cash_balance table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cash_balance (
                id INTEGER PRIMARY KEY,
                balance REAL NOT NULL
            )
        ''')
        
        # Initialize with starting cash if empty
        cursor.execute('SELECT COUNT(*) FROM cash_balance')
        if cursor.fetchone()[0] == 0:
            cursor.execute('INSERT INTO cash_balance (id, balance) VALUES (1, 500000.0)')
        
        conn.commit()
        conn.close()
    
    def get_cash_balance(self):
        """Get current cash balance"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT balance FROM cash_balance WHERE id = 1')
        balance = cursor.fetchone()[0]
        conn.close()
        return balance
    
    def update_cash_balance(self, new_balance):
        """Update cash balance"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('UPDATE cash_balance SET balance = ? WHERE id = 1', (new_balance,))
        conn.commit()
        conn.close()
    
    def execute_buy_order(self, symbol, quantity, price, strategy=""):
        """Execute buy order"""
        total_cost = quantity * price
        current_cash = self.get_cash_balance()
        
        if current_cash < total_cost:
            return False, "Insufficient funds"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check if holding exists
            cursor.execute('SELECT quantity, avg_price FROM holdings WHERE symbol = ?', (symbol,))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing holding
                old_qty, old_avg = existing
                new_qty = old_qty + quantity
                new_avg = ((old_qty * old_avg) + (quantity * price)) / new_qty
                cursor.execute('UPDATE holdings SET quantity = ?, avg_price = ? WHERE symbol = ?',
                             (new_qty, new_avg, symbol))
            else:
                # Create new holding
                cursor.execute('INSERT INTO holdings (symbol, quantity, avg_price) VALUES (?, ?, ?)',
                             (symbol, quantity, price))
            
            # Add order record
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute('''INSERT INTO orders (symbol, order_type, quantity, price, timestamp, status, strategy)
                             VALUES (?, ?, ?, ?, ?, ?, ?)''',
                          (symbol, 'BUY', quantity, price, timestamp, 'EXECUTED', strategy))
            
            # Update cash balance
            new_cash = current_cash - total_cost
            cursor.execute('UPDATE cash_balance SET balance = ? WHERE id = 1', (new_cash,))
            
            conn.commit()
            return True, "Order executed successfully"
            
        except Exception as e:
            conn.rollback()
            return False, f"Error executing order: {str(e)}"
        finally:
            conn.close()
    
    def execute_sell_order(self, symbol, quantity, price, strategy=""):
        """Execute sell order"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check holding
            cursor.execute('SELECT quantity FROM holdings WHERE symbol = ?', (symbol,))
            result = cursor.fetchone()
            
            if not result or result[0] < quantity:
                return False, "Insufficient quantity to sell"
            
            current_qty = result[0]
            
            # Update or remove holding
            if current_qty == quantity:
                cursor.execute('DELETE FROM holdings WHERE symbol = ?', (symbol,))
            else:
                cursor.execute('UPDATE holdings SET quantity = ? WHERE symbol = ?',
                             (current_qty - quantity, symbol))
            
            # Add order record
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute('''INSERT INTO orders (symbol, order_type, quantity, price, timestamp, status, strategy)
                             VALUES (?, ?, ?, ?, ?, ?, ?)''',
                          (symbol, 'SELL', quantity, price, timestamp, 'EXECUTED', strategy))
            
            # Update cash balance
            total_received = quantity * price
            current_cash = self.get_cash_balance()
            new_cash = current_cash + total_received
            cursor.execute('UPDATE cash_balance SET balance = ? WHERE id = 1', (new_cash,))
            
            conn.commit()
            return True, "Order executed successfully"
            
        except Exception as e:
            conn.rollback()
            return False, f"Error executing order: {str(e)}"
        finally:
            conn.close()
    
    def get_holdings(self):
        """Get current holdings as DataFrame"""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query('SELECT * FROM holdings', conn)
        conn.close()
        return df
    
    def get_orders(self):
        """Get order history as DataFrame"""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query('SELECT * FROM orders ORDER BY timestamp DESC', conn)
        conn.close()
        return df
    
    def get_holding_quantity(self, symbol):
        """Get quantity of specific holding"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT quantity FROM holdings WHERE symbol = ?', (symbol,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else 0
