# Options Trading Dashboard
Mini Hedge Fund - Project 1

A real-time trading dashboard for managing cryptocurrency options and futures portfolio across Binance and Bybit exchanges.

## Features

- **Real-time Portfolio Greeks Overview**: Live tracking of Delta, Gamma, Theta, and Vega for BTC and ETH
- **Risk Metrics Dashboard**: Comprehensive risk monitoring including delta exposure, hedge positions, P&L tracking
- **Multi-Exchange Positions**: View positions from both Binance and Bybit exchanges
- **Live Updates**: WebSocket-based real-time data updates every 5 seconds
- **Professional UI**: Dark-themed, responsive dashboard with color-coded status indicators

## Project Structure

```
OptionsTrading/
├── app.py                    # Flask backend with SocketIO
├── exchange_connector.py     # API connections to Binance/Bybit
├── greeks_calculator.py      # Options Greeks calculations (Black-Scholes)
├── portfolio_manager.py      # Portfolio aggregation and risk metrics
├── requirements.txt          # Python dependencies
├── env.example               # Environment variables template
├── templates/
│   └── index.html            # Dashboard HTML template
└── static/
    ├── css/
    │   └── style.css         # Dashboard styling
    └── js/
        └── dashboard.js      # Frontend JavaScript for real-time updates
```

## Setup Instructions

### 1. Create and Activate Virtual Environment

```bash
cd /Users/oguztulum/Desktop/MHF/OptionsTrading
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure API Keys

Create a `.env` file in the project root (copy from `env.example`):

```bash
cp env.example .env
```

Edit `.env` and add your API keys:

```env
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_SECRET_KEY=your_binance_secret_key_here
BYBIT_API_KEY=your_bybit_api_key_here
BYBIT_SECRET_KEY=your_bybit_secret_key_here
USE_TESTNET=true  # Use testnet for testing
```

**Getting API Keys:**
- **Binance**: https://www.binance.com/en/my/settings/api-management
- **Bybit**: https://www.bybit.com/app/user/api-management

**Note**: For testing, use testnet API keys and set `USE_TESTNET=true` in `.env`

### 4. Run the Application

```bash
python app.py
```

The dashboard will be available at: **http://localhost:5001**

**Note**: If no API keys are configured, the app will run in mock data mode.

## Usage

1. **Start the server**: Run `python app.py` in your terminal
2. **Open browser**: Navigate to `http://localhost:5001`
3. **View dashboard**: The dashboard will automatically connect and start receiving real-time updates

**First Time Setup:**
- If you see warnings about missing API keys, the app will run in mock data mode
- Add your API keys to `.env` file to enable real exchange data
- Check the terminal logs for connection status

### Dashboard Sections

- **Portfolio Greeks**: View real-time Delta, Gamma, Theta, and Vega for BTC and ETH
- **Risk Metrics**: Monitor delta exposure, hedge positions, daily P&L, portfolio value, and hedge ratio
- **Positions**: See all open positions from Binance and Bybit exchanges
- **Recent Activity**: Track the last 5 trading activities

### Status Indicators

- 🟢 **Green**: Values within safe thresholds
- 🟡 **Yellow**: Values approaching warning levels
- 🔴 **Red**: Values outside acceptable ranges

## Technical Details

- **Backend**: Flask with Flask-SocketIO for WebSocket support
- **Exchange APIs**: CCXT library for unified Binance and Bybit access
- **Greeks Calculation**: Black-Scholes model using scipy
- **Frontend**: HTML5, CSS3, JavaScript with Socket.IO client
- **Real-time Updates**: Background thread updates data every 10 seconds (respects API rate limits)
- **Data Format**: JSON-based data exchange between frontend and backend

### Key Components

- **ExchangeConnector**: Handles API connections to Binance and Bybit
- **GreeksCalculator**: Calculates Delta, Gamma, Theta, Vega using Black-Scholes
- **PortfolioManager**: Aggregates positions and calculates portfolio-level metrics

## Features

✅ **Real Exchange Integration**: Connects to Binance and Bybit APIs  
✅ **Options Greeks**: Calculates Delta, Gamma, Theta, Vega using Black-Scholes model  
✅ **Portfolio Aggregation**: Combines positions from multiple exchanges  
✅ **Risk Metrics**: Calculates delta exposure, hedge ratio, P&L, and more  
✅ **Real-time Updates**: Live data updates via WebSocket  
✅ **Testnet Support**: Safe testing with exchange testnets  
✅ **Error Handling**: Graceful fallback to mock data if APIs unavailable  

## Future Enhancements

- Implement hedge execution functionality
- Add position entry/exit capabilities
- Include historical P&L charts
- Add alerting system for risk thresholds
- Support for additional assets and exchanges
- Options chain visualization
- Implied volatility surface

## Troubleshooting

### API Connection Issues

- **Check API keys**: Ensure `.env` file has correct keys
- **Testnet mode**: Use `USE_TESTNET=true` for testing
- **Rate limits**: App updates every 10 seconds to respect limits
- **Logs**: Check terminal output for connection status

### No Positions Showing

- Verify you have open positions on the exchanges
- Check API key permissions (read-only is sufficient)
- Ensure positions are in futures/options markets (not spot)

### Greeks Not Calculating

- Options require strike, expiry, and option type
- Default volatility is 80% if not available from exchange
- Expired options will show zero Greeks

