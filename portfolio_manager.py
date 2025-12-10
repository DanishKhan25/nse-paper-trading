import sqlite3
import pandas as pd
from datetime import datetime
import streamlit as st
import json
import os
from io import StringIO

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
        
        # Try to restore from backup if database is empty
        self.restore_from_backup()
    
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
            success = True
            return True, "Order executed successfully"
            
        except Exception as e:
            conn.rollback()
            return False, f"Error executing order: {str(e)}"
        finally:
            conn.close()
            # Auto-backup after successful order
            if 'success' in locals():
                self.backup_data()
    
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
            success = True
            return True, "Order executed successfully"
            
        except Exception as e:
            conn.rollback()
            return False, f"Error executing order: {str(e)}"
        finally:
            conn.close()
            # Auto-backup after successful order
            if 'success' in locals():
                self.backup_data()
    
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
    
    def backup_data(self):
        """Backup portfolio data to session state"""
        try:
            backup_data = {
                'holdings': self.get_holdings().to_dict('records'),
                'orders': self.get_orders().to_dict('records'),
                'cash_balance': self.get_cash_balance(),
                'backup_time': datetime.now().isoformat()
            }
            st.session_state['portfolio_backup'] = backup_data
        except Exception as e:
            st.warning(f"Backup failed: {str(e)}")
    
    def restore_from_backup(self):
        """Restore portfolio data from session state if database is empty"""
        try:
            # Check if database has any orders
            orders_df = self.get_orders()
            if not orders_df.empty:
                return  # Database has data, no need to restore
            
            # Check if backup exists
            if 'portfolio_backup' not in st.session_state:
                return
            
            backup = st.session_state['portfolio_backup']
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Restore cash balance
            cursor.execute('UPDATE cash_balance SET balance = ? WHERE id = 1', (backup['cash_balance'],))
            
            # Restore holdings
            for holding in backup['holdings']:
                cursor.execute('''INSERT OR REPLACE INTO holdings (symbol, quantity, avg_price) 
                                 VALUES (?, ?, ?)''',
                              (holding['symbol'], holding['quantity'], holding['avg_price']))
            
            # Restore orders
            for order in backup['orders']:
                cursor.execute('''INSERT INTO orders (symbol, order_type, quantity, price, timestamp, status, strategy)
                                 VALUES (?, ?, ?, ?, ?, ?, ?)''',
                              (order['symbol'], order['order_type'], order['quantity'], 
                               order['price'], order['timestamp'], order['status'], order.get('strategy', '')))
            
            conn.commit()
            conn.close()
            st.success(f"✅ Portfolio restored from backup ({backup['backup_time'][:16]})")
            
        except Exception as e:
            st.warning(f"Restore failed: {str(e)}")
    
    def export_data(self):
        """Export portfolio data as JSON for download"""
        try:
            export_data = {
                'holdings': self.get_holdings().to_dict('records'),
                'orders': self.get_orders().to_dict('records'),
                'cash_balance': self.get_cash_balance(),
                'export_time': datetime.now().isoformat()
            }
            return json.dumps(export_data, indent=2)
        except Exception as e:
            st.error(f"Export failed: {str(e)}")
            return None
    
    def import_data(self, json_data):
        """Import portfolio data from JSON"""
        try:
            data = json.loads(json_data)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Clear existing data
            cursor.execute('DELETE FROM holdings')
            cursor.execute('DELETE FROM orders')
            cursor.execute('UPDATE cash_balance SET balance = ?', (data['cash_balance'],))
            
            # Import holdings
            for holding in data['holdings']:
                cursor.execute('''INSERT INTO holdings (symbol, quantity, avg_price) 
                                 VALUES (?, ?, ?)''',
                              (holding['symbol'], holding['quantity'], holding['avg_price']))
            
            # Import orders
            for order in data['orders']:
                cursor.execute('''INSERT INTO orders (symbol, order_type, quantity, price, timestamp, status, strategy)
                                 VALUES (?, ?, ?, ?, ?, ?, ?)''',
                              (order['symbol'], order['order_type'], order['quantity'], 
                               order['price'], order['timestamp'], order['status'], order.get('strategy', '')))
            
            conn.commit()
            conn.close()
            
            # Update backup
            self.backup_data()
            return True, "Portfolio imported from JSON successfully"
            
        except Exception as e:
            return False, f"JSON import failed: {str(e)}"
    
    def export_data_csv(self):
        """Export portfolio data as CSV files"""
        try:
            holdings_df = self.get_holdings()
            orders_df = self.get_orders()
            cash_balance = self.get_cash_balance()
            
            # Create CSV data
            holdings_csv = holdings_df.to_csv(index=False) if not holdings_df.empty else "symbol,quantity,avg_price\n"
            orders_csv = orders_df.to_csv(index=False) if not orders_df.empty else "id,symbol,order_type,quantity,price,timestamp,status,strategy\n"
            cash_csv = f"balance\n{cash_balance}"
            
            return holdings_csv, orders_csv, cash_csv
        except Exception as e:
            st.error(f"CSV export failed: {str(e)}")
            return None, None, None
    
    def import_data_csv(self, holdings_csv, orders_csv, cash_csv):
        """Import portfolio data from CSV files"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Clear existing data
            cursor.execute('DELETE FROM holdings')
            cursor.execute('DELETE FROM orders')
            
            # Import cash balance
            cash_df = pd.read_csv(StringIO(cash_csv))
            new_balance = float(cash_df['balance'].iloc[0])
            cursor.execute('UPDATE cash_balance SET balance = ?', (new_balance,))
            
            # Import holdings
            holdings_df = pd.read_csv(StringIO(holdings_csv))
            if not holdings_df.empty:
                for _, row in holdings_df.iterrows():
                    cursor.execute('''INSERT INTO holdings (symbol, quantity, avg_price) 
                                     VALUES (?, ?, ?)''',
                                  (row['symbol'], row['quantity'], row['avg_price']))
            
            # Import orders
            orders_df = pd.read_csv(StringIO(orders_csv))
            if not orders_df.empty:
                for _, row in orders_df.iterrows():
                    cursor.execute('''INSERT INTO orders (symbol, order_type, quantity, price, timestamp, status, strategy)
                                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                                  (row['symbol'], row['order_type'], row['quantity'], 
                                   row['price'], row['timestamp'], row['status'], row.get('strategy', '')))
            
            conn.commit()
            conn.close()
            
            # Update backup
            self.backup_data()
            return True, "Portfolio imported from CSV successfully"
            
        except Exception as e:
            return False, f"CSV import failed: {str(e)}"
