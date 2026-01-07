# Quick Setup Guide

## Step-by-Step Setup

### 1. Navigate to Project Directory
```bash
cd /Users/oguztulum/Desktop/MHF/OptionsTrading
```

### 2. Create Virtual Environment (if not already created)
```bash
python3 -m venv venv
```

### 3. Activate Virtual Environment

**On macOS/Linux:**
```bash
source venv/bin/activate
```

**On Windows:**
```bash
venv\Scripts\activate
```

You should see `(venv)` at the beginning of your terminal prompt.

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

If you get an error, try:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Configure API Keys (Optional but Recommended)

**For Real Exchange Data:**

1. Create a `.env` file in the project root:
```bash
cp env.example .env
```

2. Edit `.env` and add your API keys:
```env
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_SECRET_KEY=your_binance_secret_key_here
BYBIT_API_KEY=your_bybit_api_key_here
BYBIT_SECRET_KEY=your_bybit_secret_key_here
USE_TESTNET=true  # Use testnet for safe testing
```

**Getting API Keys:**
- **Binance**: https://www.binance.com/en/my/settings/api-management
- **Bybit**: https://www.bybit.com/app/user/api-management

**Note**: 
- For testing, use testnet API keys and set `USE_TESTNET=true`
- If no API keys are provided, the app will run in mock data mode
- Only "Read" permissions are needed (no trading permissions required)

### 6. Run the Application
```bash
python app.py
```

You should see output like:
```
🚀 Starting Options Trading Dashboard...
✅ Portfolio manager initialized
✅ Dashboard server ready on http://0.0.0.0:5001
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5001
```

**Note**: The app now runs on port **5001** (port 5000 is often used by macOS AirPlay)

### 7. Open in Browser
Open your web browser and go to:
```
http://localhost:5001
```

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'flask'"
**Solution:** Make sure your virtual environment is activated and run:
```bash
pip install -r requirements.txt
```

### Issue: "Port 5000 already in use"
**Solution:** The app now uses port 5001 by default. If you need a different port, modify `app.py` (change `port=5001` to your desired port)

### Issue: "Permission denied" when creating venv
**Solution:** Check folder permissions or try:
```bash
python3 -m venv venv --without-pip
```

### Issue: WebSocket connection not working
**Solution:** 
1. Make sure you're accessing via `http://localhost:5000` (not `https://`)
2. Check browser console for errors (F12 → Console tab)
3. Ensure Flask-SocketIO is properly installed

### Issue: Dashboard shows "Connecting..." forever
**Solution:**
1. Check browser console (F12) for WebSocket errors
2. Make sure the Flask server is running
3. Try refreshing the page

## Testing the Connection

Once the app is running, you should see:
- ✅ "Connected" status (green dot) in the top right
- ✅ Data updating every 10 seconds (real API mode) or 5 seconds (mock mode)
- ✅ Numbers changing in real-time
- ✅ Last Update timestamp updating

**Check Terminal Logs:**
- Look for connection status messages:
  - `✅ Binance connection successful` - Real API connected
  - `✅ Bybit connection successful` - Real API connected
  - `⚠️ Using mock data mode` - No API keys, using simulated data

## Stopping the Server

Press `Ctrl+C` in the terminal where the server is running.

