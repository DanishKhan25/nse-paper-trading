import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import mplfinance as mpf
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from portfolio_manager import PortfolioManager
from data_fetcher import (
    get_historical_data, get_current_price, get_stock_fundamentals,
    calculate_sma, get_nifty_500_symbols, extract_symbol
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

    # Add trading background styling
    st.markdown("""
    <style>
    .stApp {
        background-image: url('https://images.unsplash.com/photo-1633158829875-e5316a358c6f?q=80&w=1770&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D');
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }
    .stApp::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.6);
        z-index: -1;
    }
    .login-container {
        background: rgba(255, 255, 255, 0.95);
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
        backdrop-filter: blur(15px);
        border: 1px solid rgba(255, 255, 255, 0.3);
        margin-top: 5rem;
    }
    .trading-icons {
        font-size: 2rem;
        margin: 1rem 0;
        opacity: 0.8;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

    # Center the password form
    col1, col2, col3 = st.columns([1, 1, 1])

    with col2:
        st.markdown('<div class="trading-icons">📈 📊 💹 📉 💰</div>', unsafe_allow_html=True)
        st.title("🔒 NSE Paper Trading App")
        st.markdown("**Welcome to Your Trading Dashboard**")
        st.text_input("Password", type="password", on_change=password_entered, key="password", placeholder="Enter your password")

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

def create_renko_chart(data, symbol, brick_size_pct=1.0):
    """Create Renko chart using mplfinance"""
    if data is None or data.empty:
        return None
    
    try:
        # Prepare data for mplfinance - flatten multi-level columns if needed
        ohlcv = data.copy()
        
        # If columns are multi-level, flatten them
        if isinstance(ohlcv.columns, pd.MultiIndex):
            ohlcv.columns = ohlcv.columns.droplevel(1)
        
        # Ensure we have the right columns
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        if not all(col in ohlcv.columns for col in required_cols):
            st.error(f"Missing required columns. Available: {ohlcv.columns.tolist()}")
            return None
        
        # Select only OHLCV columns
        ohlcv = ohlcv[required_cols]
        
        # Calculate brick size based on current price
        current_price = float(ohlcv['Close'].iloc[-1])
        brick_size = current_price * (brick_size_pct / 100)
        
        # Renko parameters
        renko_params = dict(brick_size=brick_size)
        
        # Create the plot without ax parameter
        fig, axes = mpf.plot(
            ohlcv,
            type="renko",
            renko_params=renko_params,
            style="charles",
            title=f"Renko Chart - {symbol} (Brick Size: {brick_size_pct}%)",
            figsize=(12, 6),
            returnfig=True
        )
        
        return fig
        
    except Exception as e:
        st.error(f"Error creating Renko chart: {str(e)}")
        return None

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
    
    # Backup/Restore Section
    st.markdown("---")
    st.subheader("💾 Data Backup")
    
    # Export section
    st.write("**📥 Export Portfolio**")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("JSON Export", help="Download as single JSON file"):
            export_data = portfolio.export_data()
            if export_data:
                st.download_button(
                    label="Download JSON",
                    data=export_data,
                    file_name=f"portfolio_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                    mime="application/json"
                )
    
    with col2:
        if st.button("CSV Export", help="Download as separate CSV files"):
            holdings_csv, orders_csv, cash_csv = portfolio.export_data_csv()
            if holdings_csv and orders_csv and cash_csv:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M')
                
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.download_button("Holdings CSV", holdings_csv, f"holdings_{timestamp}.csv", "text/csv")
                with col_b:
                    st.download_button("Orders CSV", orders_csv, f"orders_{timestamp}.csv", "text/csv")
                with col_c:
                    st.download_button("Cash CSV", cash_csv, f"cash_{timestamp}.csv", "text/csv")
    
    # Import section
    st.write("**📤 Import Portfolio**")
    import_type = st.radio("Import Type", ["JSON", "CSV"], horizontal=True)
    
    if import_type == "JSON":
        uploaded_file = st.file_uploader("Upload JSON backup", type="json")
        if uploaded_file:
            json_data = uploaded_file.read().decode()
            success, message = portfolio.import_data(json_data)
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)
    
    else:  # CSV
        st.write("Upload all three CSV files:")
        holdings_file = st.file_uploader("Holdings CSV", type="csv", key="holdings_csv")
        orders_file = st.file_uploader("Orders CSV", type="csv", key="orders_csv")
        cash_file = st.file_uploader("Cash CSV", type="csv", key="cash_csv")
        
        if holdings_file and orders_file and cash_file:
            holdings_csv = holdings_file.read().decode()
            orders_csv = orders_file.read().decode()
            cash_csv = cash_file.read().decode()
            
            success, message = portfolio.import_data_csv(holdings_csv, orders_csv, cash_csv)
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)

# Main content
# st.title("📈 NSE Paper Trading App")
# st.markdown("---")

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs(["🔄 Trade", "💼 Holdings", "📋 Order Book", "📊 Analysis"])

# Tab 1 - Trade
with tab1:
    col1, col2 = st.columns([1, 2])



        # Stock selector with search
    with col1:
        st.subheader("Place Order")
        symbols = get_nifty_500_symbols()
        selected_display = st.selectbox("Select Stock", symbols, key="trade_symbol")
        selected_symbol = extract_symbol(selected_display)
        
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
                # Store success info in session state
                st.session_state.order_success = {
                    'type': order_type,
                    'symbol': selected_symbol,
                    'quantity': quantity,
                    'price': price,
                    'total': total_value,
                    'strategy': strategy
                }
                st.rerun()
            else:
                st.error(f"❌ {message}")
    with col2:
        # Show success popup if order was just executed
        if 'order_success' in st.session_state:
            order_info = st.session_state.order_success
            st.success("🎉 ORDER EXECUTED SUCCESSFULLY! 🎉")
            st.info(f"📋 **Order Details:**\n- **Type:** {order_info['type']}\n- **Stock:** {order_info['symbol']}\n- **Quantity:** {order_info['quantity']}\n- **Price:** ₹{order_info['price']:.2f}\n- **Total:** ₹{order_info['total']:,.2f}")
            if order_info['strategy']:
                st.info(f"📝 **Strategy:** {order_info['strategy']}")
            st.balloons()
            # Clear the success state
            del st.session_state.order_success
    

    
    # Renko Chart below order form
    st.subheader(f"📊 {selected_symbol} ")
    
    hist_data = get_historical_data(selected_symbol, "1y")
    if hist_data is not None and not hist_data.empty:
        current_price_display = get_current_price(selected_symbol)
        brick_size_pct = 1.0
        if current_price_display:
            st.info(f"Current: ₹{current_price_display:.2f} | Brick: {brick_size_pct}% (₹{current_price_display * brick_size_pct / 100:.2f})")
        
        renko_fig = create_renko_chart(hist_data, selected_symbol, brick_size_pct)
        
        if renko_fig:
            st.pyplot(renko_fig)
        else:
            st.warning("Unable to generate Renko chart")
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
        st.dataframe(df_display, use_container_width=True)
        
        # Renko Chart for Holdings
        st.subheader("📊 Renko Chart - Holdings Analysis")
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.write("**Holdings Watchlist**")
            
            # Initialize selected holding index
            if 'selected_holding_idx' not in st.session_state:
                st.session_state.selected_holding_idx = 0
            
            holding_symbols = holdings_df['symbol'].tolist()


            if holding_symbols:
                # Create watchlist container
                watchlist_container = st.container()
                
                with watchlist_container:
                    for i, symbol in enumerate(holding_symbols):
                        # Get current price for display
                        current_price = current_prices.get(symbol, 0)
                        
                        # Create clickable row
                        if st.button(
                            f"{symbol} - ₹{current_price:.2f}",
                            key=f"holding_watch_{i}",
                            use_container_width=True,
                            type="primary" if i == st.session_state.selected_holding_idx else "secondary"
                        ):
                            st.session_state.selected_holding_idx = i

        
        with col2:
            if holding_symbols:
                selected_holding = holding_symbols[st.session_state.selected_holding_idx]
                
                # Display Renko chart for selected holding
                hist_data = get_historical_data(selected_holding, "6mo")
                if hist_data is not None and not hist_data.empty:
                    current_price = get_current_price(selected_holding)
                    brick_size_pct = 1.0
                    if current_price:
                        st.info(f"**{selected_holding}** - Current: ₹{current_price:.2f} | Brick: {brick_size_pct}% (₹{current_price * brick_size_pct / 100:.2f})")

                    renko_fig = create_renko_chart(hist_data, selected_holding, brick_size_pct)
                    
                    if renko_fig:
                        st.pyplot(renko_fig)
                    else:
                        st.warning("Unable to generate Renko chart")
                else:
                    st.error("Unable to load data for Renko chart")
            else:
                st.info("No holdings available for chart analysis")

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
        
        # Renko Chart for Order Book
        st.subheader("📊 Renko Chart - Order Analysis")
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.write("**Order Symbols Watchlist**")
            
            # Initialize selected order symbol index
            if 'selected_order_idx' not in st.session_state:
                st.session_state.selected_order_idx = 0
            
            order_symbols = orders_df['symbol'].unique().tolist()
            
            if order_symbols:
                # Create watchlist container
                watchlist_container = st.container()
                
                with watchlist_container:
                    for i, symbol in enumerate(order_symbols):
                        # Get current price for display
                        current_price = get_current_price(symbol)
                        price_display = f"₹{current_price:.2f}" if current_price else "N/A"
                        
                        # Create clickable row
                        if st.button(
                            f"{symbol} - {price_display}",
                            key=f"order_watch_{i}",
                            use_container_width=True,
                            type="primary" if i == st.session_state.selected_order_idx else "secondary"
                        ):
                            st.session_state.selected_order_idx = i


        with col2:
            if order_symbols:
                selected_order_symbol = order_symbols[st.session_state.selected_order_idx]
                
                # Display Renko chart for selected symbol
                hist_data = get_historical_data(selected_order_symbol, "6mo")
                if hist_data is not None and not hist_data.empty:
                    current_price = get_current_price(selected_order_symbol)
                    brick_size_pct = 1.0
                    if current_price:
                        st.info(f"**{selected_order_symbol}** - Current: ₹{current_price:.2f} | Brick: {brick_size_pct}% (₹{current_price * brick_size_pct / 100:.2f})")
                    
                    renko_fig = create_renko_chart(hist_data, selected_order_symbol, brick_size_pct)
                    
                    if renko_fig:
                        st.pyplot(renko_fig)
                    else:
                        st.warning("Unable to generate Renko chart")
                else:
                    st.error("Unable to load data for Renko chart")
            else:
                st.info("No order symbols available for chart analysis")
        
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
    # Create TradingView-style layout
    col_watchlist, col_main = st.columns([1, 3])
    
    with col_watchlist:
        # Add CSS for scrollable watchlist
        st.markdown("""
        <style>
        .watchlist-container {
            height: 400px;
            overflow-y: scroll;
            border: 1px solid #e0e0e0;
            border-radius: 5px;
            padding: 5px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Search functionality
        search_query = st.text_input("Search stocks", placeholder="Type symbol...", key="watchlist_search")
        
        # Sort options
        sort_option = st.selectbox("Sort by", ["Alphabetical", "Volume (High to Low)", "Volume (Low to High)"], key="sort_option")
        
        # Get all stocks for watchlist
        all_symbols = get_nifty_500_symbols()
        
        # Filter stocks based on search
        if search_query:
            filtered_stocks = [s for s in all_symbols if search_query.upper() in s.upper()]
        else:
            filtered_stocks = all_symbols  # Show all stocks by default
        
        # Sort stocks based on selection
        if sort_option.startswith("Volume"):
            if len(filtered_stocks) > 100:
                st.warning("⚠️ Volume sorting for large lists may take time. Consider searching to narrow down first.")
            
            try:
                with st.spinner("Sorting by volume..."):
                    # Get volume data for sorting
                    volume_data = {}
                    for stock_display in filtered_stocks:
                        symbol = extract_symbol(stock_display)
                        hist_data = get_historical_data(symbol, "1d")
                        if hist_data is not None and not hist_data.empty:
                            volume_data[stock_display] = hist_data['Volume'].iloc[-1] if 'Volume' in hist_data.columns else 0
                        else:
                            volume_data[stock_display] = 0
                    
                    # Sort by volume
                    if sort_option == "Volume (High to Low)":
                        filtered_stocks = sorted(filtered_stocks, key=lambda x: volume_data.get(x, 0), reverse=True)
                    else:  # Volume (Low to High)
                        filtered_stocks = sorted(filtered_stocks, key=lambda x: volume_data.get(x, 0))
                        
            except Exception as e:
                st.error("Volume sorting failed, showing alphabetical order")
        # Alphabetical is default, no sorting needed as symbols are already sorted
        
        # Initialize selected stock index
        if 'selected_analysis_idx' not in st.session_state:
            st.session_state.selected_analysis_idx = 0
        
        # Reset index if out of bounds
        if filtered_stocks and st.session_state.selected_analysis_idx >= len(filtered_stocks):
            st.session_state.selected_analysis_idx = 0
        
        # Navigation buttons at the top
        col_up, col_down = st.columns(2)
        with col_up:
            if st.button("⬆️", key="analysis_up", use_container_width=True):
                if filtered_stocks:
                    st.session_state.selected_analysis_idx = (st.session_state.selected_analysis_idx - 1) % len(filtered_stocks)
                    st.rerun()
        with col_down:
            if st.button("⬇️", key="analysis_down", use_container_width=True):
                if filtered_stocks:
                    st.session_state.selected_analysis_idx = (st.session_state.selected_analysis_idx + 1) % len(filtered_stocks)
                    st.rerun()
        
        # Create watchlist
        if filtered_stocks:
            # Use Streamlit's native container with height
            with st.container(height=400):
                for i, stock_display in enumerate(filtered_stocks):
                    symbol = extract_symbol(stock_display)
                    
                    # Create clickable stock row (no price fetching)
                    if st.button(
                        symbol,
                        key=f"analysis_stock_{i}",
                        use_container_width=True,
                        type="primary" if i == st.session_state.selected_analysis_idx else "secondary"
                    ):
                        st.session_state.selected_analysis_idx = i
                        st.rerun()
            
            # Get selected symbol
            selected_display = filtered_stocks[st.session_state.selected_analysis_idx]
            analysis_symbol = extract_symbol(selected_display)
        else:
            analysis_symbol = "RELIANCE"
    
    with col_main:
        # Charts section at the top
        st.subheader(f"📈 {analysis_symbol} - Charts")
        if current_price_display:
            st.info(
                f"Current: ₹{current_price_display:.2f} | Brick: {brick_size_pct}% (₹{current_price_display * brick_size_pct / 100:.2f})")

        # Timeframe selector
        timeframe = st.radio("Select Timeframe", ["6 Months", "1 Year"], horizontal=True)
        period = "6mo" if timeframe == "6 Months" else "1y"
        
        # Get historical data based on selected timeframe
        hist_data = get_historical_data(analysis_symbol, period)

        # Renko Chart (moved to top)
        st.write(f"**{timeframe} Renko Chart**")

        if hist_data is not None and not hist_data.empty:
            current_price_display = get_current_price(analysis_symbol)
            brick_size_pct = 1.0

            renko_fig = create_renko_chart(hist_data, analysis_symbol, brick_size_pct)

            if renko_fig:
                st.pyplot(renko_fig)
            else:
                st.warning("Unable to generate Renko chart")
        else:
            st.error("Unable to load data for Renko chart")

        # Candlestick Chart with Moving Averages (moved to bottom)
        st.write(f"**{timeframe} Chart with Moving Averages**")
        
        if hist_data is not None and not hist_data.empty:
            # Prepare data for mplfinance
            ohlcv = hist_data.copy()
            
            # If columns are multi-level, flatten them
            if isinstance(ohlcv.columns, pd.MultiIndex):
                ohlcv.columns = ohlcv.columns.droplevel(1)
            
            # Calculate moving averages
            sma_20 = calculate_sma(hist_data, 20)
            sma_50 = calculate_sma(hist_data, 50)
            
            # Create addplots for moving averages
            apds = []
            if sma_20 is not None:
                apds.append(mpf.make_addplot(sma_20, color='#FF6B35', width=2))
            if sma_50 is not None:
                apds.append(mpf.make_addplot(sma_50, color='#004E89', width=2))
            
            # Custom style for cleaner look
            mc = mpf.make_marketcolors(
                up='#00C851',
                down='#FF4444', 
                edge='inherit',
                wick={'up':'#00C851', 'down':'#FF4444'},
                volume='in'
            )
            
            s = mpf.make_mpf_style(
                marketcolors=mc,
                gridstyle='-',
                gridcolor='#E0E0E0',
                facecolor='white',
                figcolor='white'
            )
            
            # Create the candlestick chart
            fig, axes = mpf.plot(
                ohlcv,
                type='candle',
                style=s,
                title=f"{analysis_symbol} - {timeframe} Analysis",
                figsize=(12, 6),
                addplot=apds if apds else None,
                returnfig=True,
                tight_layout=True
            )
            
            st.pyplot(fig)
        else:
            st.error("Unable to load chart data")
        
        # Fundamentals section below charts
        st.subheader("📈 Fundamentals")
    
    fundamentals = get_stock_fundamentals(analysis_symbol)
    
    if fundamentals:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if fundamentals.get('pe_ratio'):
                st.metric("P/E Ratio", f"{fundamentals['pe_ratio']:.2f}")
            if fundamentals.get('market_cap'):
                st.metric("Market Cap", format_inr(fundamentals['market_cap']))
        
        with col2:
            if fundamentals.get('pb_ratio'):
                st.metric("P/B Ratio", f"{fundamentals['pb_ratio']:.2f}")
            if fundamentals.get('roe'):
                st.metric("ROE", f"{fundamentals['roe']*100:.2f}%")
        
        with col3:
            if fundamentals.get('debt_equity'):
                st.metric("Debt/Equity", f"{fundamentals['debt_equity']:.2f}")
            if fundamentals.get('dividend_yield'):
                st.metric("Dividend Yield", f"{fundamentals['dividend_yield']*100:.2f}%")
        
        with col4:
            if fundamentals.get('week_52_high'):
                st.metric("52W High", f"₹{fundamentals['week_52_high']:.2f}")
            if fundamentals.get('week_52_low'):
                st.metric("52W Low", f"₹{fundamentals['week_52_low']:.2f}")
    else:
        st.warning("Unable to fetch fundamental data")

# Footer
st.markdown("---")
st.markdown("**Disclaimer:** This is a paper trading application for educational purposes only. Not for real trading.")
