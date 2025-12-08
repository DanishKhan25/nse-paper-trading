# NSE Paper Trading App

A Streamlit-based paper trading application for learning swing trading in the Indian stock market (NSE).

## Features

- **Virtual Portfolio**: Start with ₹5 lakh virtual capital
- **Real NSE Data**: Live stock prices and historical data via yfinance
- **Complete Trading**: Buy/sell stocks with paper money
- **Portfolio Tracking**: Real-time P&L calculation
- **Technical Analysis**: Candlestick charts with moving averages
- **Fundamental Analysis**: Key financial metrics
- **Order Management**: Complete order book with strategy tagging

## File Structure

```
swing-trader-app/
├── app.py                 # Main Streamlit application
├── portfolio_manager.py   # Portfolio and database operations
├── data_fetcher.py       # NSE data fetching with caching
├── requirements.txt      # Python dependencies
├── README.md            # This file
└── trading.db           # SQLite database (auto-created)
```

## Local Setup Instructions

### 1. Clone/Download the Project
```bash
cd /path/to/your/project
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Application
```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## Usage Guide

### Trading Tab
1. Select a stock from the dropdown
2. Choose BUY or SELL
3. Enter quantity and price (defaults to current market price)
4. Add optional strategy tag
5. Click "Execute Order"

### Holdings Tab
- View all current positions
- See real-time P&L with color coding
- Track invested vs current value

### Order Book Tab
- Complete transaction history
- Filter by strategy tags
- View order statistics

### Analysis Tab
- Deep dive into any stock
- View fundamental metrics
- 1-year price chart with SMA 20/50 overlays

## Deployment to Streamlit Cloud

### 1. Push to GitHub
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/nse-paper-trading.git
git push -u origin main
```

### 2. Deploy on Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Connect your GitHub account
3. Select your repository
4. Set main file path: `app.py`
5. Click "Deploy"

### 3. Configuration
- The app will automatically install dependencies from `requirements.txt`
- SQLite database will be created automatically on first run
- No additional configuration needed

## Technical Details

### Data Sources
- **Stock Prices**: yfinance library (Yahoo Finance API)
- **NSE Symbols**: Popular Nifty 500 stocks included
- **Caching**: 24-hour cache for historical data, 30-minute for current prices

### Database Schema
- **holdings**: symbol, quantity, avg_price
- **orders**: symbol, order_type, quantity, price, timestamp, status, strategy
- **cash_balance**: current available cash

### Key Features
- **Portfolio Calculations**: Automatic average price calculation on multiple buys
- **Error Handling**: Graceful handling of API failures and invalid orders
- **Real-time Updates**: Live P&L calculation with current market prices
- **Indian Formatting**: All amounts displayed in INR format

## Limitations

- **Educational Use Only**: This is a paper trading app, not for real trading
- **NSE Stocks Only**: Limited to Indian equity markets
- **Daily Data**: Suitable for swing trading, not intraday
- **Free Tier**: Uses free APIs with reasonable rate limits

## Troubleshooting

### Common Issues

1. **"Module not found" errors**
   ```bash
   pip install -r requirements.txt
   ```

2. **Data fetching errors**
   - Check internet connection
   - Verify stock symbol is correct (NSE format)
   - Some stocks may have limited data availability

3. **Database errors**
   - Delete `trading.db` file to reset (will lose all data)
   - Ensure write permissions in app directory

### Performance Tips
- Historical data is cached for 24 hours
- Current prices cached for 30 minutes
- Restart app if experiencing slow performance

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Verify all dependencies are installed correctly
3. Ensure you're using the correct NSE stock symbols

---

**Disclaimer**: This application is for educational purposes only. It simulates trading with virtual money and should not be used for actual investment decisions.
