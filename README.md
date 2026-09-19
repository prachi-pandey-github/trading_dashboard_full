# ⚡ Professional Stock Trading Dashboard

A comprehensive stock analysis dashboard built with Streamlit, featuring TradingView-style charts, AI-powered analysis using Groq, and interactive chart replay functionality.

## ✨ Features

### 📊 Interactive Trading Chart
- **TradingView-style candlestick charts** with professional dark theme
- **Support and resistance zones** visualization
- **Trading signals** (LONG/SHORT/Neutral) with visual markers
- **Multiple timeframes** (1D, 1W, 1M, 3M, 1Y, ALL)
- **Real-time filtering** and responsive design

### 🤖 AI-Powered Analysis
- **Groq AI integration** for intelligent data analysis
- **Natural language queries** about your stock data
- **Pre-built sample questions** for quick insights
- **Chat history** to track your analysis sessions
- **Automated insights** on trading patterns and performance

### ▶️ Chart Replay Feature
- **Time-based replay** of historical price action
- **Variable speed control** (0.5x to 10x speed)
- **Progress tracking** with visual indicators
- **Pause/Resume** functionality for detailed analysis

### 📈 Market Overview
- **Key metrics dashboard** with trading statistics
- **Performance indicators** and price change tracking
- **Signal distribution** analysis (Long vs Short vs Neutral)
- **Volume analysis** and trading day statistics

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup Instructions

1. **Clone or download the project files**
    ```bash
    # If using git
    git clone <repository-url>
    cd trading_dashboard
    
    # Or download and extract the files
    ```

2. **Install required packages**
    ```bash
    pip install -r requirements.txt
    ```

3. **Configure API Keys (Required for data and AI features)**
    - Get your Groq API key from [Groq Console](https://console.groq.com/)
    - Get your Alpha Vantage API key from [Alpha Vantage](https://www.alphavantage.co/support/#api-key)
    - Replace the placeholders in `.env` file:
    ```
    GROQ_API_KEY=YOUR_ACTUAL_GROQ_API_KEY
    GROQ_MODEL=openai/gpt-oss-20b
    ALPHAVANTAGE_API_KEY=YOUR_ACTUAL_ALPHAVANTAGE_API_KEY
    ```

4. **Run the application**
    ```bash
    streamlit run eg.py
    ```

5. **Access the dashboard**
    - Open your browser and navigate to `http://localhost:8501`

## 🌐 Separate HTML Frontend

The original Streamlit app remains available and unchanged. A separate responsive frontend is served by a lightweight FastAPI adapter that delegates data filtering, summaries, and Groq analysis to the existing `TSLADashboard` class.

### Run the frontend

```bash
uvicorn backend.api:app --reload
```

Open `http://localhost:8000`. The adapter serves `frontend/` and exposes `/api/data`, `/api/summary`, `/api/data/upload`, `/api/data/alphavantage`, `/api/ask`, and `/api/auth/config`. Enter a ticker in the frontend's **Stock symbol** field to fetch Alpha Vantage data using `ALPHAVANTAGE_API_KEY` from `.env`.

### Supabase authentication

Copy `.env.example` to `.env` and set `SUPABASE_URL` and `SUPABASE_ANON_KEY` from your Supabase project's API settings. Enable Email authentication in Supabase Auth. The frontend uses Supabase's browser client for sign-up, sign-in, email confirmation, and persisted sessions; only the public anon key is exposed to the browser. Never put the `service_role` key in `.env` for this app.

### Run both experiences

Use separate terminals if you want both interfaces available:

```bash
streamlit run eg.py
uvicorn backend.api:app --reload --port 8000
```

The HTML frontend owns presentation and browser replay state. The API layer only adapts request/response formats and reuses the existing Python dashboard logic; it does not replace or modify the Streamlit app.

## 📁 Data Sources

The dashboard supports two data sources:

### 1. Alpha Vantage API
- Enter any stock symbol (e.g., TSLA, AAPL, GOOGL, MSFT)
- Fetches daily time series data automatically
- Requires `ALPHAVANTAGE_API_KEY` in `.env`

### 2. CSV Upload
Upload your own stock data CSV file with the following columns:

| Column | Type | Description | Required |
|--------|------|-------------|----------|
| Date | datetime | Trading date (YYYY-MM-DD) | ✅ Yes |
| Open | float | Opening price | ✅ Yes |
| High | float | Highest price of the day | ✅ Yes |
| Low | float | Lowest price of the day | ✅ Yes |
| Close | float | Closing price | ✅ Yes |
| Volume | integer | Trading volume | ✅ Yes |
| direction | string | Trading signal ('LONG', 'SHORT', 'N') | ✅ Yes |
| Support | list/string | Support levels (e.g., "[180.5, 175.2]") | ⚠️ Optional |
| Resistance | list/string | Resistance levels (e.g., "[220.8, 225.4]") | ⚠️ Optional |

### Sample CSV Data
```csv
Date,Open,High,Low,Close,Volume,direction,Support,Resistance
2024-01-15,195.50,198.75,192.30,196.80,12500000,LONG,"[185.2, 180.5]","[205.8, 210.4]"
```

### Bundled Data
A sample `TSLA_data.csv` is included in the `data/` folder for testing.

## 🎯 Usage Guide

### 1. Loading Data
- **Alpha Vantage API**: Select "Alpha Vantage API" in the sidebar, enter a stock symbol, and click "Fetch Data"
- **CSV Upload**: Select "Upload CSV" in the sidebar and upload your stock data file
- **Data Validation**: The app automatically validates required columns

### 2. Chart Analysis
- **Time Periods**: Click buttons (1D, 1W, 1M, 3M, 1Y, ALL) to filter data
- **Visual Signals**: 
  - 🟢 **Green arrows up**: LONG signals
  - 🔴 **Red arrows down**: SHORT signals  
  - 🟡 **Yellow dots**: Neutral signals
- **Support/Resistance**: Green and red shaded zones show key levels

### 3. AI Analysis
- **Sample Questions**: Click pre-built questions for quick insights
- **Custom Queries**: Type your own questions about the data
- **Chat History**: Review previous AI responses
- **Example Questions**:
  - "How many bullish days were in this period?"
  - "What was the highest closing price and when did it occur?"
  - "How many LONG vs SHORT signals were generated?"

### 4. Chart Replay
- **Speed Control**: Adjust replay speed from 0.5x to 10x
- **Controls**: Start/Pause, Reset functionality
- **Progress**: Visual progress bar and day counter

## 🛠️ Technical Details

### Architecture
- **Frontend**: Streamlit with custom CSS styling
- **Charts**: streamlit-lightweight-charts for TradingView-style visualization
- **AI Engine**: Groq AI (llama-3.1-8b-instant) for natural language analysis
- **Data Sources**: Alpha Vantage API or local CSV files
- **Data Processing**: Pandas and NumPy for data manipulation

### Key Components
- **TSLADashboard Class**: Main application logic
- **Chart Generation**: Dynamic candlestick chart creation
- **Data Filtering**: Time-based data filtering system
- **AI Integration**: Groq AI query processing
- **State Management**: Streamlit session state for replay functionality

### Project Structure
```
trading_dashboard/
├── eg.py                 # Main Streamlit application
├── backend/
│   └── api.py            # FastAPI adapter for the separate frontend
├── frontend/
│   ├── index.html        # Frontend structure
│   ├── styles.css        # Responsive visual system
│   └── app.js            # Chart, controls, replay, and API client
├── requirements.txt      # Python dependencies
├── .env                  # API keys (not committed)
├── .gitignore           # Git ignore rules
├── data/
│   └── TSLA_data.csv    # Sample TSLA data
├── test.py              # Alpha Vantage API test script
└── README.md            # This file
```

## 🔧 Customization

### Styling
The dashboard uses a professional dark theme with TradingView-inspired colors:
- **Background**: Deep blue (#0f0f23)
- **Accent**: Cyan (#00d4aa)
- **Bull/Long**: Green (#00d4aa)
- **Bear/Short**: Red (#ff4976)

### Extending Functionality
- **Add new indicators**: Modify the chart creation function
- **Custom AI prompts**: Enhance the AI query system
- **Additional timeframes**: Add new filtering options
- **Export features**: Add data download capabilities

## ⚠️ Important Notes

### Security
- **API Keys**: Never commit your API keys to version control
- **Environment Variables**: API keys are loaded from `.env` file
- **Git Ignore**: `.env` is included in `.gitignore` to prevent accidental commits

### Performance
- **Large Datasets**: Performance may vary with very large datasets (>10K rows)
- **Replay Speed**: Higher speeds may cause browser performance issues
- **Memory Usage**: Monitor memory usage with large CSV files

### Limitations
- **Data Dependencies**: Alpha Vantage free tier has API call limits
- **AI Rate Limits**: Groq AI has usage limits based on your plan
- **Browser Compatibility**: Best viewed in modern browsers (Chrome, Firefox, Safari)

## 🐛 Troubleshooting

### Common Issues

1. **"No module named 'streamlit'"**
    ```bash
    pip install streamlit
    ```

2. **"API key error"**
    - Verify your Groq API key is correct
    - Check API key permissions and quotas
    - Ensure `.env` file is in the project root

3. **"CSV format error"**
    - Ensure your CSV has the required columns: Date, Open, High, Low, Close, Volume, direction
    - Check date format (YYYY-MM-DD)
    - Ensure column names match exactly (case-sensitive)

4. **"Alpha Vantage API error"**
    - Verify your Alpha Vantage API key is correct
    - Check API call frequency limits (free tier: 25 calls/day, 5 calls/minute)
    - Ensure stock symbol is valid

5. **Chart not displaying**
    - Check browser console for JavaScript errors
    - Try refreshing the page

### Getting Help
- Check the Streamlit documentation: https://docs.streamlit.io/
- Groq AI documentation: https://console.groq.com/docs
- Alpha Vantage documentation: https://www.alphavantage.co/documentation/
- Create an issue in the project repository

## 📜 License

This project is provided as-is for educational and personal use. Please ensure compliance with relevant financial data regulations in your jurisdiction.

## 🤝 Contributing

Feel free to submit issues, feature requests, or pull requests to improve the dashboard.

---

**Happy Trading! 📈⚡**
