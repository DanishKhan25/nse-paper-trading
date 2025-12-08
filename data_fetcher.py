import yfinance as yf
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

@st.cache_data(ttl=86400)  # 24 hour cache for historical data
def get_historical_data(symbol, period="3y"):
    """Fetch historical OHLC data for NSE stocks"""
    try:
        # Add .NS suffix for NSE stocks
        ticker = f"{symbol}.NS"
        stock = yf.Ticker(ticker)
        data = stock.history(period=period)
        
        if data.empty:
            return None
        
        return data
    except Exception as e:
        st.error(f"Error fetching historical data for {symbol}: {str(e)}")
        return None

@st.cache_data(ttl=1800)  # 30 minute cache for current prices
def get_current_price(symbol):
    """Fetch current price for NSE stock"""
    try:
        ticker = f"{symbol}.NS"
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Try different price fields
        current_price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose')
        
        if current_price:
            return float(current_price)
        
        # Fallback: get latest close from history
        hist = stock.history(period="1d")
        if not hist.empty:
            return float(hist['Close'].iloc[-1])
            
        return None
    except Exception as e:
        st.warning(f"Error fetching current price for {symbol}: {str(e)}")
        return None

@st.cache_data(ttl=86400)  # 24 hour cache for fundamentals
def get_stock_fundamentals(symbol):
    """Fetch fundamental data for NSE stock"""
    try:
        ticker = f"{symbol}.NS"
        stock = yf.Ticker(ticker)
        info = stock.info
        
        fundamentals = {
            'pe_ratio': info.get('trailingPE'),
            'pb_ratio': info.get('priceToBook'),
            'market_cap': info.get('marketCap'),
            'roe': info.get('returnOnEquity'),
            'debt_equity': info.get('debtToEquity'),
            'dividend_yield': info.get('dividendYield'),
            'week_52_high': info.get('fiftyTwoWeekHigh'),
            'week_52_low': info.get('fiftyTwoWeekLow'),
            'avg_volume': info.get('averageVolume'),
            'sector': info.get('sector'),
            'industry': info.get('industry')
        }
        
        return fundamentals
    except Exception as e:
        st.warning(f"Error fetching fundamentals for {symbol}: {str(e)}")
        return {}

def calculate_sma(data, window):
    """Calculate Simple Moving Average"""
    if data is not None and not data.empty:
        return data['Close'].rolling(window=window).mean()
    return None

def get_nifty_500_symbols():
    """Return a list of popular NSE symbols for autocomplete"""
    # Sample of popular NSE stocks - in production, this could be loaded from a file
    symbols = [
        'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'HINDUNILVR', 'ICICIBANK', 'KOTAKBANK',
        'BHARTIARTL', 'ITC', 'SBIN', 'LT', 'ASIANPAINT', 'AXISBANK', 'MARUTI', 'NESTLEIND',
        'HCLTECH', 'WIPRO', 'ULTRACEMCO', 'BAJFINANCE', 'TITAN', 'SUNPHARMA', 'ONGC',
        'NTPC', 'POWERGRID', 'TECHM', 'TATAMOTORS', 'COALINDIA', 'BAJAJFINSV', 'HDFCLIFE',
        'BRITANNIA', 'DIVISLAB', 'CIPLA', 'DRREDDY', 'EICHERMOT', 'GRASIM', 'HINDALCO',
        'INDUSINDBK', 'JSWSTEEL', 'M&M', 'ONGC', 'SBILIFE', 'SHREECEM', 'TATASTEEL',
        'TATACONSUM', 'UPL', 'VEDL', 'ADANIPORTS', 'APOLLOHOSP', 'BAJAJ-AUTO', 'BPCL',
        'HEROMOTOCO', 'IOC', 'PIDILITIND', 'TRENT'
    ]
    return sorted(symbols)
