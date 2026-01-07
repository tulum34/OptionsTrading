"""
Real-time Trading Dashboard - Flask Backend
Manages cryptocurrency options and futures portfolio across Binance and Bybit
"""

import os
import logging
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import threading
import time
from datetime import datetime
from dotenv import load_dotenv

# Import our custom modules
from exchange_connector import ExchangeConnector
from greeks_calculator import GreeksCalculator
from portfolio_manager import PortfolioManager

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here-change-in-production')
socketio = SocketIO(app, cors_allowed_origins="*")

# Global trading data state
trading_data = {
    'btc': {
        'delta': 0.0,
        'gamma': 0.0,
        'theta': 0.0,
        'vega': 0.0
    },
    'eth': {
        'delta': 0.0,
        'gamma': 0.0,
        'theta': 0.0,
        'vega': 0.0
    },
    'risk_metrics': {
        'delta_exposure': 0.0,
        'hedge_position': {'btc': 0.0, 'eth': 0.0},
        'net_risk': 0.0,
        'margin_used': 0.0,
        'daily_pnl': 0.0,
        'daily_pnl_pct': 0.0,
        'portfolio_value': 0.0,
        'hedge_ratio': 0.0
    },
    'positions': {
        'binance': [],
        'bybit': []
    },
    'recent_activity': [],
    'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
}

# Initialize exchange connectors and portfolio manager
portfolio_manager = None


def initialize_connectors():
    """Initialize exchange connectors and portfolio manager"""
    global portfolio_manager
    
    try:
        # Get API keys from environment variables
        binance_api_key = os.getenv('BINANCE_API_KEY', '')
        binance_secret = os.getenv('BINANCE_SECRET_KEY', '')
        bybit_api_key = os.getenv('BYBIT_API_KEY', '')
        bybit_secret = os.getenv('BYBIT_SECRET_KEY', '')
        
        # Check if testnet mode
        use_testnet = os.getenv('USE_TESTNET', 'false').lower() == 'true'
        
        # Initialize exchange connectors
        binance_connector = None
        bybit_connector = None
        
        if binance_api_key and binance_secret:
            try:
                binance_connector = ExchangeConnector(
                    'binance',
                    binance_api_key,
                    binance_secret,
                    testnet=use_testnet
                )
                if binance_connector.test_connection():
                    logger.info("✅ Binance connection successful")
                else:
                    logger.warning("⚠️ Binance connection test failed")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Binance connector: {e}")
        else:
            logger.warning("⚠️ Binance API keys not found in .env file")
        
        if bybit_api_key and bybit_secret:
            try:
                bybit_connector = ExchangeConnector(
                    'bybit',
                    bybit_api_key,
                    bybit_secret,
                    testnet=use_testnet
                )
                if bybit_connector.test_connection():
                    logger.info("✅ Bybit connection successful")
                else:
                    logger.warning("⚠️ Bybit connection test failed")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Bybit connector: {e}")
        else:
            logger.warning("⚠️ Bybit API keys not found in .env file")
        
        # Initialize Greeks calculator
        risk_free_rate = float(os.getenv('RISK_FREE_RATE', '0.05'))
        default_volatility = float(os.getenv('DEFAULT_VOLATILITY', '0.80'))
        greeks_calculator = GreeksCalculator(
            risk_free_rate=risk_free_rate,
            default_volatility=default_volatility
        )
        
        # Initialize portfolio manager (use None connectors if not available)
        if binance_connector or bybit_connector:
            portfolio_manager = PortfolioManager(
                binance_connector or ExchangeConnector('binance', '', '', testnet=use_testnet),
                bybit_connector or ExchangeConnector('bybit', '', '', testnet=use_testnet),
                greeks_calculator
            )
            logger.info("✅ Portfolio manager initialized")
        else:
            logger.error("❌ No exchange connectors available. Please check your .env file.")
            logger.info("💡 Using mock data mode. Add API keys to .env to enable real data.")
            portfolio_manager = None
        
    except Exception as e:
        logger.error(f"❌ Error initializing connectors: {e}")
        portfolio_manager = None


def update_trading_data():
    """Update trading data from real exchanges or use mock data"""
    global trading_data
    
    while True:
        try:
            if portfolio_manager:
                # Fetch real data from exchanges
                logger.info("🔄 Fetching real-time portfolio data...")
                dashboard_data = portfolio_manager.get_dashboard_data()
                
                # Update global trading data
                trading_data = dashboard_data
                
                logger.info(f"✅ Updated portfolio data: {len(trading_data['positions']['binance'])} Binance, "
                          f"{len(trading_data['positions']['bybit'])} Bybit positions")
            else:
                # Fallback to mock data if no API keys configured
                logger.warning("⚠️ Using mock data mode (no API keys configured)")
                _update_mock_data()
            
            # Emit update to all connected clients
            socketio.emit('update', trading_data)
            
        except Exception as e:
            logger.error(f"❌ Error updating trading data: {e}")
            # On error, keep existing data but update timestamp
            trading_data['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            socketio.emit('update', trading_data)
        
        # Wait 10 seconds before next update (to respect API rate limits)
        time.sleep(10)


def _update_mock_data():
    """Fallback mock data generator (for testing without API keys)"""
    import random
    
    # Simple mock data updates
    trading_data['btc']['delta'] = random.uniform(-0.5, 0.5)
    trading_data['btc']['gamma'] = random.uniform(0, 0.2)
    trading_data['btc']['theta'] = random.uniform(-100, -10)
    trading_data['btc']['vega'] = random.uniform(50, 200)
    
    trading_data['eth']['delta'] = random.uniform(-0.5, 0.5)
    trading_data['eth']['gamma'] = random.uniform(0, 0.2)
    trading_data['eth']['theta'] = random.uniform(-100, -10)
    trading_data['eth']['vega'] = random.uniform(50, 200)
    
    trading_data['risk_metrics']['delta_exposure'] = trading_data['btc']['delta'] + trading_data['eth']['delta']
    trading_data['risk_metrics']['daily_pnl'] = random.uniform(-1000, 2000)
    trading_data['risk_metrics']['portfolio_value'] = random.uniform(100000, 200000)
    trading_data['risk_metrics']['daily_pnl_pct'] = (trading_data['risk_metrics']['daily_pnl'] / 
                                                     trading_data['risk_metrics']['portfolio_value']) * 100
    trading_data['risk_metrics']['hedge_ratio'] = random.uniform(70, 95)
    
    trading_data['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')


@app.route('/')
def index():
    """Serve the main dashboard page"""
    return render_template('index.html')


@app.route('/api/data')
def get_data():
    """API endpoint to get current trading data"""
    return trading_data


@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info('Client connected')
    # Send initial data on connect
    emit('update', trading_data)


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info('Client disconnected')


@socketio.on('request_update')
def handle_request_update():
    """Handle manual update request from client"""
    logger.info('Manual update requested')
    if portfolio_manager:
        try:
            dashboard_data = portfolio_manager.get_dashboard_data()
            global trading_data
            trading_data = dashboard_data
            emit('update', trading_data)
        except Exception as e:
            logger.error(f"Error handling update request: {e}")
    else:
        emit('update', trading_data)


if __name__ == '__main__':
    # Initialize connectors on startup
    logger.info("🚀 Starting Options Trading Dashboard...")
    initialize_connectors()
    
    # Start background thread for data updates
    update_thread = threading.Thread(target=update_trading_data, daemon=True)
    update_thread.start()
    
    logger.info("✅ Dashboard server ready on http://0.0.0.0:5001")
    logger.info("📊 Open http://localhost:5001 in your browser")
    
    # Run Flask app with SocketIO
    socketio.run(app, host='0.0.0.0', port=5001, debug=True, allow_unsafe_werkzeug=True)
