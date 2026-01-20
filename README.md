# Binance SPOT Trading Bot

A production-ready, modular trading bot for Binance SPOT markets with a clear multi-timeframe trend-following strategy, strict risk management, and comprehensive logging.

## ⚠️ Disclaimer

This bot is for educational purposes. Trading cryptocurrencies carries significant risk. Never trade with money you cannot afford to lose. Always test thoroughly in dry-run mode before live trading.

## 🎯 Features

- **Multi-timeframe Strategy**: Combines 5m and 15m timeframes for signal confirmation
- **Clear Entry/Exit Rules**: EMA trend filter + RSI + Volume confirmation
- **Strict Risk Management**: Maximum 1% risk per trade, dynamic position sizing
- **One Position at a Time**: Simple, focused trading approach
- **Exchange-Aware**: Respects Binance minNotional and stepSize limits
- **Comprehensive Logging**: All trades logged to CSV, detailed console output
- **Dry-Run Mode**: Test strategies without risking real capital
- **Error Handling**: Robust error handling and reconnection logic

## 📋 Requirements

- Python 3.10 or higher
- Binance account with API keys
- Minimum balance: ~$50 (depends on trading pair and minNotional)

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/ucal54/ucal54bot.git
cd ucal54bot
```

### 2. Install Dependencies

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure API Keys

```bash
cp .env.example .env
# Edit .env and add your Binance API credentials
```

Create API keys at: https://www.binance.com/en/my/settings/api-management

**Required API Permissions:**
- ✅ Enable Reading
- ✅ Enable Spot & Margin Trading
- ❌ Enable Withdrawals (NOT needed)

**Security Tips:**
- Restrict API access to your IP address
- Never share your API keys
- Use API keys with minimal permissions

### 4. Configure Bot Settings

```bash
cp config/config.example.yml config/config.yml
# Edit config/config.yml to customize settings
```

Key settings to configure:
- `symbol`: Trading pair (e.g., BTCUSDT, ETHUSDT)
- `dry_run`: Set to `true` for testing, `false` for live trading
- Strategy parameters (EMAs, RSI, etc.)

### 5. Run the Bot

**Dry-run mode (recommended for testing):**
```bash
python main.py
```

**Live trading (after thorough testing):**
```bash
# Set dry_run: false in config/config.yml
python main.py
```

## 📊 Strategy Overview

See [STRATEGY.md](STRATEGY.md) for detailed strategy explanation.

**Quick Summary:**
- **Timeframes**: 5m (fast) + 15m (slow) for confirmation
- **Trend Filter**: EMA 50 and EMA 200
- **Entry Signal**: Price above EMA200, EMA50 > EMA200, RSI 40-60, Volume > Average
- **Take Profit**: +1.2%
- **Stop Loss**: -0.6%
- **Max Duration**: 45 minutes
- **Emergency Exit**: EMA50 crosses below EMA200

## 📁 Project Structure

```
ucal54bot/
├── bot/
│   ├── __init__.py
│   ├── trader.py              # Main bot orchestrator
│   ├── strategy.py            # Trading strategy logic
│   ├── risk_manager.py        # Risk management & position sizing
│   ├── data_fetcher.py        # Market data fetching
│   └── utils/
│       ├── __init__.py
│       ├── logger.py          # Logging setup
│       ├── config_loader.py   # Configuration loader
│       └── trade_logger.py    # Trade logging to CSV
├── config/
│   └── config.example.yml     # Configuration template
├── main.py                    # Entry point
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variables template
├── README.md                 # This file
├── STRATEGY.md               # Strategy explanation
└── DEPLOYMENT.md             # VPS deployment guide
```

## 📈 Monitoring

### Console Output

The bot logs all activity to console:
- Market data fetching
- Entry/exit signals
- Trade execution
- Position status
- PnL updates

### Log Files

- **Daily logs**: `logs/bot_YYYYMMDD.log`
- **Trade history**: `trades.csv`

### Trade Log Format

The `trades.csv` file contains:
- Timestamp
- Symbol
- Side (BUY/SELL)
- Entry/Exit prices
- Quantity
- PnL and PnL%
- Exit reason
- Trade duration

## ⚙️ Configuration

### Trading Settings

```yaml
trading:
  symbol: "BTCUSDT"    # Trading pair
  dry_run: true        # Enable dry-run mode
```

### Strategy Parameters

```yaml
strategy:
  timeframes:
    fast: "5m"         # Fast timeframe
    slow: "15m"        # Slow timeframe
  
  indicators:
    ema_fast: 50       # Fast EMA period
    ema_slow: 200      # Slow EMA period
    rsi_period: 14     # RSI period
    volume_sma: 20     # Volume SMA period
```

### Risk Management

```yaml
risk:
  max_risk_per_trade_pct: 1.0    # Maximum 1% risk per trade
  max_open_positions: 1           # Only 1 position at a time
```

## 🔧 Troubleshooting

### Common Issues

**1. "Configuration file not found"**
```bash
cp config/config.example.yml config/config.yml
```

**2. "Missing Binance API credentials"**
```bash
cp .env.example .env
# Edit .env and add your API keys
```

**3. "Insufficient balance"**
- Ensure you have enough USDT in your SPOT wallet
- Check the minNotional requirement for your trading pair
- Try a different symbol with lower minimum

**4. "Position size calculated as 0"**
- Your balance may be too low for the minimum trade size
- The minNotional requirement may be too high
- Try a different trading pair

**5. API errors**
- Check your API key permissions
- Ensure SPOT trading is enabled
- Verify your IP is whitelisted (if restriction enabled)

### Getting Help

If you encounter issues:
1. Check the log files in `logs/` directory
2. Enable DEBUG logging in config.yml
3. Verify your API keys and permissions
4. Test with dry_run: true first

## 🚨 Safety Notes

### Before Going Live

1. **Test thoroughly in dry-run mode** for at least a few days
2. **Start with small capital** to test in live mode
3. **Monitor the first few trades** closely
4. **Set up proper API restrictions** (IP whitelist, no withdrawal permissions)
5. **Keep your API keys secure** and never commit them to git

### Known Limitations

- **LONG positions only** - Does not trade SHORT
- **One position at a time** - No portfolio management
- **Market orders only** - May have slippage on illiquid pairs
- **No advanced features** - No grid, martingale, or complex strategies
- **Requires stable internet** - Connection issues may miss exits

### Failure Cases

The bot will log errors and continue running if:
- API rate limits are hit
- Network connectivity issues
- Invalid order sizes
- Insufficient balance

The bot will exit if:
- Fatal configuration errors
- Unable to connect to Binance API
- Keyboard interrupt (Ctrl+C)

On shutdown or fatal error, the bot attempts to close any open positions.

## 📚 Additional Documentation

- [STRATEGY.md](STRATEGY.md) - Detailed strategy explanation and logic
- [DEPLOYMENT.md](DEPLOYMENT.md) - How to deploy on Linux VPS

## 🛠️ Development

### Running Tests

```bash
# TODO: Add tests
pytest tests/
```

### Code Style

The code follows Python best practices:
- Type hints where applicable
- Comprehensive docstrings
- Modular, single-responsibility design
- Clear error handling

## 📝 License

This project is provided as-is for educational purposes.

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## ⭐ Support

If you find this bot useful, please give it a star on GitHub!

---

**Remember: Never risk more than you can afford to lose. Cryptocurrency trading is highly risky.**
