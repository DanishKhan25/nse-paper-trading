Prompt for APP   
I want to build a paper trading web app for learning swing trading in the Indian stock market (NSE). This is for personal use only, not for production.

## Requirements

### Core Functionality
1. Virtual portfolio with ₹5 lakh starting capital
2. Buy/sell NSE stocks with paper money
3. Track holdings with real-time P&L (profit/loss)
4. Complete order book showing all transactions
5. Stock analysis with technical indicators and fundamentals

### Technical Stack
- **Backend + Frontend**: Python with Streamlit (single language for simplicity)
- **Database**: SQLite SQLite Persistence (local, no server needed)
- **Data Source**: yfinance library (fetches real NSE India data)
- **Caching**: Streamlit's built-in @st.cache_data (24-hour cache for historical, 30-min for current prices)
- **Charts**: Plotly for interactive candlestick charts
- **Deployment**: Should be deployable on Streamlit Cloud (free tier)

### Data Requirements
- Historical daily OHLC data (3 year)
- Current stock prices (15-min delayed is fine)
- Fundamental data: P/E ratio, P/B ratio, Market Cap, ROE, Debt/Equity, Dividend Yield
- Technical indicators: SMA 20, SMA 50 (basic moving averages)
- Support for nifty 500  NSE stocks.

### UI Design (Desktop-Focused)
**4 Main Tabs:**

**Tab 1 - Trade:**
- Stock selector dropdown text field with autosuggestions (NSE symbols)
- Buy/Sell radio buttons
- Current price display
- Quantity input
- Price input (editable, defaults to current price)
- Total value calculation
- Execute order button
Tag for which strategy we buy this. in orders we can filter by strategy 
- 6-month candlestick chart on the right side

**Tab 2 - Holdings:**
- Table showing: Symbol, Quantity, Avg Price, Current Price, Invested Value, Current Value, P&L, P&L%
- Color-coded P&L (green for profit, red for loss)

**Tab 3 - Order Book:**
- Transaction history table: Timestamp, Symbol, Type (BUY/SELL), Quantity, Price, Status,stratergy tag
- Sorted by most recent first
- Show all orders  - strategy analysis - average holding time 
-win and loss etc

**Tab 4 - Analysis:**
- Stock selector for deep dive
- Fundamentals section (PE, PB, ROE, etc.)
- Key metrics (52W High/Low, Avg Volume)
- 1-year price chart with SMA 20 and SMA 50 overlays

**Sidebar:** should be collapsing 
- Portfolio summary:
  - Total Portfolio Value
  - Cash Available
  - Total P&L (₹ and %)
- Display all in Indian Rupee format (₹)

### Database Schema
**Tables:**
1. `holdings`: symbol, quantity, avg_price (tracks current positions)
2. `orders`: symbol, order_type, quantity, price, timestamp, status (transaction log)
3. `cash_balance`: balance (single row with current cash)

### Key Features
- Start with ₹500,000 virtual cash
- When buying: Check sufficient funds, deduct cash, update holdings (calculate new avg price if adding to existing position)
- When selling: Check sufficient quantity, add cash, reduce holdings (delete row if quantity becomes 0)
- All prices in INR (Indian Rupees)
- Cache historical data for 24 hours (reduces API calls)
- Cache current prices for 30 minutes
- Handle errors gracefully (show warnings if data unavailable)

### Important Implementation Details
1. Use yfinance library functions:
   - `equity_history(symbol, "EQ", start_date, end_date)` for historical data
   - `nse_quote_ltp(symbol)` for current price
   - `nse_eq(symbol)` for fundamentals

2. Date format for NSE API: "dd-mm-yyyy"

3. For price input field, ensure default value is never 0.0 (use 100.0 as fallback if current_price is None)

4. Use Plotly candlestick charts: `go.Candlestick(x, open, high, low, close)`

5. Store portfolio state in SQLite, not session_state (persistent across restarts)

6. Initialize database with tables on first run

7. Calculate average price on multiple buys: `new_avg = ((old_qty * old_avg) + (new_qty * new_price)) / total_qty`

### File Structure
swing-trader-app/
├── app.py # Main Streamlit app (UI + all tabs)
├── portfolio_manager.py # Portfolio logic (database operations, order execution)
├── data_fetcher.py # NSE data fetching with caching
├── requirements.txt
└── trading.db # SQLite (auto-created on first run) 


### Error Handling
- If NSE API fails, show warning and allow manual price entry
- If stock data unavailable, show error message in chart area
- Validate order execution (sufficient funds/quantity) before placing
- Show success/error messages after each action

### Nice-to-Have Features
- Balloons animation on successful order
- Color-coded metrics (green for positive P&L, red for negative)
- Wide layout mode for desktop
- Helpful tooltips and captions
- INR formatting with commas (₹1,23,456.78)

### Constraints
- Swing trading focus (daily data is sufficient, no intraday)
- Only equities (no options/futures)
- Desktop-first design (not mobile-optimized)
- Single-user (no authentication needed)
- Free deployment (no paid APIs or services)

## Deliverables
Please provide:
1. Complete code for all 3 Python files
2. requirements.txt with exact versions
3. Step-by-step instructions to run locally
4. Instructions for deploying to Streamlit Cloud

Write production-quality code with proper error handling, comments, and following Python best practices. I don’t want mock data real data from NSE 
 