import yfinance as yf
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import warnings
import requests
import os
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

@st.cache_data(ttl=86400)  # 24 hour cache
def get_nifty_500_symbols():
    """Fetch NSE symbols from NSE website with local CSV fallback"""
    local_file = 'sec_list.csv'
    
    try:
        # Try downloading from NSE
        url = 'https://nsearchives.nseindia.com/content/equities/sec_list.csv'
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Save to local file
        with open(local_file, 'wb') as f:
            f.write(response.content)
        
        # Read and parse
        df = pd.read_csv(local_file)
        symbols = df['Symbol'].dropna().unique().tolist()
        return sorted(symbols)
        
    except Exception as e:
        # Fallback to local file
        if os.path.exists(local_file):
            try:
                df = pd.read_csv(local_file)
                symbols = df['Symbol'].dropna().unique().tolist()
                return sorted(symbols)
            except:
                pass
        
        # Final fallback to hardcoded list
        return sorted([
            'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'HINDUNILVR', 'ICICIBANK', 'KOTAKBANK',
            'BHARTIARTL', 'ITC', 'SBIN', 'LT', 'ASIANPAINT', 'AXISBANK', 'MARUTI', 'NESTLEIND',
            'HCLTECH', 'WIPRO', 'ULTRACEMCO', 'BAJFINANCE', 'TITAN', 'SUNPHARMA', 'ONGC',
            'NTPC', 'POWERGRID', 'TECHM', 'TATAMOTORS', 'COALINDIA', 'BAJAJFINSV', 'HDFCLIFE'
        ])
