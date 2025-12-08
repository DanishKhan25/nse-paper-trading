import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
from portfolio_manager import PortfolioManager
from data_fetcher import (
    get_historical_data, get_current_price, get_stock_fundamentals,
    calculate_sma, get_nifty_500_symbols
)

# Page config
st.set_page_config(
    page_title="NSE Paper Trading App",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Password protection
def check_password():
    """Returns True if user entered correct password."""
    def password_entered():
        if st.session_state["password"] == st.secrets.get("password", "trading123"):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    st.title("🔒 NSE Paper Trading App")
    st.text_input("Password", type="password", on_change=password_entered, key="password")
    
    if "password_correct" in st.session_state and not st.session_state["password_correct"]:
        st.error("😕 Password incorrect")
    
    return False

if not check_password():
    st.stop()

# Initialize portfolio manager
@st.cache_resource
def init_portfolio():
    return PortfolioManager()

portfolio = init_portfolio()

# Helper functions
def format_inr(amount):
    """Format amount in Indian Rupee format"""
    if amount >= 10000000:  # 1 crore
        return f"₹{amount/10000000:.2f}Cr"
    elif amount >= 100000:  # 1 lakh
        return f"₹{amount/100000:.2f}L"
    else:
        return f"₹{amount:,.2f}"

def calculate_portfolio_value(holdings_df, current_prices):
    """Calculate total portfolio value"""
    total_value = 0
    for _, row in holdings_df.iterrows():
        current_price = current_prices.get(row['symbol'], 0)
        total_value += row['quantity'] * current_price
    return total_value

# Sidebar - Portfolio Summary
with st.sidebar:
    st.header("📊 Portfolio Summary")
    
    cash_balance = portfolio.get_cash_balance()
    holdings_df = portfolio.get_holdings()
    
    # Get current prices for all holdings
    current_prices = {}
    total_invested = 0
    total_current = 0
    
    if not holdings_df.empty:
        for symbol in holdings_df['symbol'].unique():
            price = get_current_price(symbol)
            current_prices[symbol] = price if price else 0
        
        for _, row in holdings_df.iterrows():
            invested = row['quantity'] * row['avg_price']
            current = row['quantity'] * current_prices.get(row['symbol'], 0)
            total_invested += invested
            total_current += current
    
    total_portfolio = cash_balance + total_current
    total_pnl = total_current - total_invested
    pnl_pct = (total_pnl / total_invested * 100) if total_invested > 0 else 0
    
    st.metric("Total Portfolio Value", format_inr(total_portfolio))
    st.metric("Cash Available", format_inr(cash_balance))
    
    if total_invested > 0:
        st.metric(
            "Total P&L", 
            format_inr(total_pnl),
            delta=f"{pnl_pct:.2f}%"
        )

# Main content
st.title("📈 NSE Paper Trading App")
st.markdown("---")

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs(["🔄 Trade", "💼 Holdings", "📋 Order Book", "📊 Analysis"])

# Tab 1 - Trade
with tab1:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Place Order")
        
        # Stock selector
        symbols = get_nifty_500_symbols()
        selected_symbol = st.selectbox("Select Stock", symbols, key="trade_symbol")
        
        # Get current price
        current_price = get_current_price(selected_symbol)
        if current_price:
            st.info(f"Current Price: ₹{current_price:.2f}")
        else:
            st.warning("Unable to fetch current price")
            current_price = 100.0  # Fallback
        
        # Order type
        order_type = st.radio("Order Type", ["BUY", "SELL"])
        
        # Quantity and price
        quantity = st.number_input("Quantity", min_value=1, value=1)
        price = st.number_input("Price (₹)", min_value=0.01, value=current_price, format="%.2f")
        
        # Strategy tag
        strategy = st.text_input("Strategy Tag (optional)", placeholder="e.g., Swing Trade, Breakout")
        
        # Total value
        total_value = quantity * price
        st.info(f"Total Value: ₹{total_value:,.2f}")
        
        # Execute order button
        if st.button("Execute Order", type="primary"):
            if order_type == "BUY":
                success, message = portfolio.execute_buy_order(selected_symbol, quantity, price, strategy)
            else:
                success, message = portfolio.execute_sell_order(selected_symbol, quantity, price, strategy)
            
            if success:
                st.success(message)
                st.balloons()
                st.rerun()
            else:
                st.error(message)
    
    with col2:
        st.subheader(f"📈 {selected_symbol} - 6 Month Chart")
        
        # Get historical data
        hist_data = get_historical_data(selected_symbol, "6mo")
        
        if hist_data is not None and not hist_data.empty:
            # Create candlestick chart
            fig = go.Figure(data=go.Candlestick(
                x=hist_data.index,
                open=hist_data['Open'],
                high=hist_data['High'],
                low=hist_data['Low'],
                close=hist_data['Close'],
                name=selected_symbol
            ))
            
            fig.update_layout(
                title=f"{selected_symbol} Price Chart",
                yaxis_title="Price (₹)",
                xaxis_title="Date",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("Unable to load chart data")

# Tab 2 - Holdings
with tab2:
    st.subheader("💼 Current Holdings")
    
    holdings_df = portfolio.get_holdings()
    
    if holdings_df.empty:
        st.info("No holdings found. Start trading to see your positions here.")
    else:
        # Prepare holdings display
        display_data = []
        
        for _, row in holdings_df.iterrows():
            symbol = row['symbol']
            quantity = row['quantity']
            avg_price = row['avg_price']
            
            current_price = current_prices.get(symbol, 0)
            invested_value = quantity * avg_price
            current_value = quantity * current_price
            pnl = current_value - invested_value
            pnl_pct = (pnl / invested_value * 100) if invested_value > 0 else 0
            
            display_data.append({
                'Symbol': symbol,
                'Quantity': quantity,
                'Avg Price': f"₹{avg_price:.2f}",
                'Current Price': f"₹{current_price:.2f}",
                'Invested Value': f"₹{invested_value:,.2f}",
                'Current Value': f"₹{current_value:,.2f}",
                'P&L': f"₹{pnl:,.2f}",
                'P&L %': f"{pnl_pct:.2f}%"
            })
        
        df_display = pd.DataFrame(display_data)
        
        # Color coding for P&L
        def color_pnl(val):
            if 'P&L' in val.name:
                if val.str.contains('-').any():
                    return ['color: red' if '-' in str(v) else 'color: green' for v in val]
            return [''] * len(val)
        
        st.dataframe(df_display, use_container_width=True)

# Tab 3 - Order Book
with tab3:
    st.subheader("📋 Order History")
    
    orders_df = portfolio.get_orders()
    
    if orders_df.empty:
        st.info("No orders found. Place your first trade to see order history.")
    else:
        # Format orders for display
        orders_display = orders_df.copy()
        orders_display['Price'] = orders_display['price'].apply(lambda x: f"₹{x:.2f}")
        orders_display['Total Value'] = (orders_display['quantity'] * orders_display['price']).apply(lambda x: f"₹{x:,.2f}")
        
        # Select columns for display
        display_cols = ['timestamp', 'symbol', 'order_type', 'quantity', 'Price', 'Total Value', 'strategy', 'status']
        orders_display = orders_display[display_cols]
        orders_display.columns = ['Timestamp', 'Symbol', 'Type', 'Quantity', 'Price', 'Total Value', 'Strategy', 'Status']
        
        st.dataframe(orders_display, use_container_width=True)
        
        # Strategy analysis
        if not orders_df.empty:
            st.subheader("📊 Strategy Analysis")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                total_orders = len(orders_df)
                buy_orders = len(orders_df[orders_df['order_type'] == 'BUY'])
                sell_orders = len(orders_df[orders_df['order_type'] == 'SELL'])
                
                st.metric("Total Orders", total_orders)
                st.metric("Buy Orders", buy_orders)
                st.metric("Sell Orders", sell_orders)

# Tab 4 - Analysis
with tab4:
    st.subheader("📊 Stock Analysis")
    
    # Stock selector for analysis
    analysis_symbol = st.selectbox("Select Stock for Analysis", get_nifty_500_symbols(), key="analysis_symbol")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("📈 Fundamentals")
        
        fundamentals = get_stock_fundamentals(analysis_symbol)
        
        if fundamentals:
            metrics = [
                ("P/E Ratio", fundamentals.get('pe_ratio')),
                ("P/B Ratio", fundamentals.get('pb_ratio')),
                ("Market Cap", fundamentals.get('market_cap')),
                ("ROE", fundamentals.get('roe')),
                ("Debt/Equity", fundamentals.get('debt_equity')),
                ("Dividend Yield", fundamentals.get('dividend_yield')),
                ("52W High", fundamentals.get('week_52_high')),
                ("52W Low", fundamentals.get('week_52_low')),
                ("Avg Volume", fundamentals.get('avg_volume')),
            ]
            
            for label, value in metrics:
                if value is not None:
                    if label == "Market Cap":
                        st.metric(label, format_inr(value))
                    elif label in ["ROE", "Dividend Yield"] and value:
                        st.metric(label, f"{value*100:.2f}%")
                    elif label in ["52W High", "52W Low"]:
                        st.metric(label, f"₹{value:.2f}")
                    else:
                        st.metric(label, f"{value:.2f}" if isinstance(value, (int, float)) else str(value))
        else:
            st.warning("Unable to fetch fundamental data")
    
    with col2:
        st.subheader(f"📈 {analysis_symbol} - 1 Year Chart with Moving Averages")
        
        # Get 1-year historical data
        hist_data = get_historical_data(analysis_symbol, "1y")
        
        if hist_data is not None and not hist_data.empty:
            # Calculate moving averages
            sma_20 = calculate_sma(hist_data, 20)
            sma_50 = calculate_sma(hist_data, 50)
            
            # Create chart
            fig = go.Figure()
            
            # Add candlestick
            fig.add_trace(go.Candlestick(
                x=hist_data.index,
                open=hist_data['Open'],
                high=hist_data['High'],
                low=hist_data['Low'],
                close=hist_data['Close'],
                name=analysis_symbol
            ))
            
            # Add moving averages
            if sma_20 is not None:
                fig.add_trace(go.Scatter(
                    x=hist_data.index,
                    y=sma_20,
                    mode='lines',
                    name='SMA 20',
                    line=dict(color='orange', width=2)
                ))
            
            if sma_50 is not None:
                fig.add_trace(go.Scatter(
                    x=hist_data.index,
                    y=sma_50,
                    mode='lines',
                    name='SMA 50',
                    line=dict(color='blue', width=2)
                ))
            
            fig.update_layout(
                title=f"{analysis_symbol} - 1 Year Analysis",
                yaxis_title="Price (₹)",
                xaxis_title="Date",
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("Unable to load chart data")

# Footer
st.markdown("---")
st.markdown("**Disclaimer:** This is a paper trading application for educational purposes only. Not for real trading.")
