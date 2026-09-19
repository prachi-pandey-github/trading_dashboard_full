import streamlit as st
import pandas as pd
import numpy as np
import json
import ast
from datetime import datetime, timedelta
from groq import Groq
from typing import List, Dict, Any
import os
import requests
from streamlit_lightweight_charts import renderLightweightCharts
import time  # Added for replay feature
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure page
st.set_page_config(
page_title="Stock Analysis Dashboard",
page_icon="📈",
layout="wide",
initial_sidebar_state="expanded"
)

# CSS for TradingView-style dark theme (unchanged)
st.markdown("""
<style>
    /* Global Dark Theme */
    .stApp {
        background-color: #0f0f23;
        color: #d1d4dc;
    }
    
    /* Main container styling */
    .main .block-container {
        background-color: #0f0f23;
        padding-top: 1rem;
    }
    
    /* Header styling */
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #00d4aa;
        text-align: center;
        margin-bottom: 2rem;
        text-shadow: 0 0 10px rgba(0, 212, 170, 0.3);
    }
    
    /* Chart container */
    .chart-container {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid #2d3748;
        border-radius: 12px;
        padding: 20px;
        margin: 20px 0;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
    }
    
    /* Chart header */
    .chart-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 15px;
        padding-bottom: 10px;
        border-bottom: 1px solid #2d3748;
    }
    
    .chart-title {
        color: #00d4aa;
        font-size: 1.2rem;
        font-weight: 600;
        margin: 0;
    }
    
    /* Metrics cards */
    .metric-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid #2d3748;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    }
    
    .metric-card .metric-label {
        color: #a0aec0;
        font-size: 0.85rem;
        margin-bottom: 5px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .metric-card .metric-value {
        color: #00d4aa;
        font-size: 1.5rem;
        font-weight: bold;
        margin-bottom: 2px;
    }
    
    .metric-card .metric-delta {
        font-size: 0.8rem;
        color: #68d391;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #1a1a2e;
    }
    
    .css-1d391kg .css-10trblm {
        color: #d1d4dc;
    }
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #1a1a2e;
        border-bottom: 1px solid #2d3748;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        color: #a0aec0;
        border: none;
        padding: 12px 24px;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #2d3748;
        color: #d1d4dc;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #00d4aa !important;
        color: #0f0f23 !important;
    }
    
    /* Input styling */
    .stTextInput > div > div > input {
        background-color: #2d3748;
        color: #d1d4dc;
        border: 1px solid #4a5568;
        border-radius: 6px;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #00d4aa;
        box-shadow: 0 0 0 1px #00d4aa;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #00d4aa 0%, #00b894 100%);
        color: #0f0f23;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.5rem 1.5rem;
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0, 212, 170, 0.3);
    }
    
    /* Success/Info styling */
    .stSuccess {
        background-color: #22543d;
        border: 1px solid #38a169;
        color: #68d391;
    }
    
    .stInfo {
        background-color: #2a4365;
        border: 1px solid #3182ce;
        color: #63b3ed;
    }
    
    .stWarning {
        background-color: #744210;
        border: 1px solid #d69e2e;
        color: #f6e05e;
    }
    
    /* Legend styling */
    .legend-container {
        display: flex;
        gap: 20px;
        margin: 10px 0;
        flex-wrap: wrap;
    }
    
    .legend-item {
        display: flex;
        align-items: center;
        gap: 8px;
        background: rgba(45, 55, 72, 0.6);
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
    }
    
    .legend-dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        display: inline-block;
    }
    
    .legend-dot.support { background-color: #48bb78; }
    .legend-dot.resistance { background-color: #f56565; }
    .legend-dot.long { background-color: #38a169; }
    .legend-dot.short { background-color: #e53e3e; }
    .legend-dot.neutral { background-color: #FFD700; } 
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #1a1a2e;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #2d3748;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #4a5568;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'data' not in st.session_state:
    st.session_state.data = None
if 'time_period' not in st.session_state:
    st.session_state.time_period = 'ALL'
# Add replay state variables
if 'replay_running' not in st.session_state:
    st.session_state.replay_running = False
if 'replay_index' not in st.session_state:
    st.session_state.replay_index = 0

class TSLADashboard:
    def __init__(self):
        self.data = None
        self.groq_client = None
        self.symbol = None
        
    def setup_groq(self):
        """Setup Groq AI client"""
        try:
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                st.error("GROQ_API_KEY not found in .env file.")
                return False
            self.groq_client = Groq(api_key=api_key)
            return True
        except Exception as e:
            st.error(f"Error setting up Groq AI: {str(e)}")
            return False
    
    def fetch_data_from_alphavantage(self, symbol, api_key):
        """Fetch stock data from Alpha Vantage API"""
        try:
            url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&outputsize=compact&apikey={api_key}'
            
            response = requests.get(url)
            data = response.json()
            
            if 'Error Message' in data:
                st.error(f"API Error: {data['Error Message']}")
                return None
            
            if 'Information' in data:
                st.error(f"API Information: {data['Information']}")
                return None
            
            if 'Note' in data:
                st.warning("API call frequency limit reached. Please wait a minute before trying again.")
                return None
            
            if 'Time Series (Daily)' not in data:
                st.error(f"No data found for the given symbol. The API response was: {data}")
                return None
            
            time_series = data['Time Series (Daily)']
            
            # Convert to DataFrame
            df_data = []
            for date_str, values in time_series.items():
                df_data.append({
                    'Date': pd.to_datetime(date_str),
                    'Open': float(values['1. open']),
                    'High': float(values['2. high']),
                    'Low': float(values['3. low']),
                    'Close': float(values['4. close']),
                    'Volume': int(values['5. volume']),
                    'direction': 'N',  # Default neutral direction
                    'Support': [],
                    'Resistance': []
                })
            
            df = pd.DataFrame(df_data)
            df = df.sort_values('Date').reset_index(drop=True)
            
            # Add technical analysis (simple direction logic)
            for i in range(1, len(df)):
                if df.loc[i, 'Close'] > df.loc[i-1, 'Close']:
                    df.loc[i, 'direction'] = 'LONG'
                elif df.loc[i, 'Close'] < df.loc[i-1, 'Close']:
                    df.loc[i, 'direction'] = 'SHORT'
                else:
                    df.loc[i, 'direction'] = 'N'
            
            return df
            
        except Exception as e:
            st.error(f"Error fetching data from Alpha Vantage: {str(e)}")
            return None
    
    def load_data(self, symbol=None, api_key=None, uploaded_file=None):
        """Load and process stock data"""
        try:
            if symbol and api_key:
                # Fetch from Alpha Vantage API
                df = self.fetch_data_from_alphavantage(symbol, api_key)
                if df is None:
                    return None
                self.symbol = symbol
            elif uploaded_file is not None:
                df = pd.read_csv(uploaded_file)
                
                # Ensure Date column exists and is datetime
                if 'Date' not in df.columns:
                    st.error("CSV must contain a 'Date' column")
                    return None
                df['Date'] = pd.to_datetime(df['Date'])
            else:
                # Sample data structure for demonstration
                dates = pd.date_range(start='2022-08-25', end='2025-05-02', freq='D')
                np.random.seed(42)
                
                base_price = 200
                prices = []
                current_price = base_price
                
                for i in range(len(dates)):
                    daily_change = np.random.normal(0, 5)
                    current_price = max(50, current_price + daily_change)
                    
                    open_price = current_price
                    high_price = open_price + abs(np.random.normal(0, 3))
                    low_price = open_price - abs(np.random.normal(0, 3))
                    close_price = low_price + (high_price - low_price) * np.random.random()
                    volume = np.random.randint(1000000, 10000000)
                    
                    direction_prob = np.random.random()
                    if direction_prob < 0.3:
                        direction = 'LONG'
                    elif direction_prob < 0.6:
                        direction = 'SHORT'
                    else:
                        direction = 'N'
                    
                    support_levels = [low_price - np.random.uniform(5, 15) for _ in range(2, 5)]
                    resistance_levels = [high_price + np.random.uniform(5, 15) for _ in range(2, 5)]
                    
                    prices.append({
                        'Date': dates[i],
                        'Open': round(open_price, 2),
                        'High': round(high_price, 2),
                        'Low': round(low_price, 2),
                        'Close': round(close_price, 2),
                        'Volume': volume,
                        'direction': direction,
                        'Support': support_levels,
                        'Resistance': resistance_levels
                    })
                
                df = pd.DataFrame(prices)
            
            df['Date'] = pd.to_datetime(df['Date'])
            
            if 'Support' in df.columns and isinstance(df['Support'].iloc[0], str):
                df['Support'] = df['Support'].apply(lambda x: ast.literal_eval(x) if pd.notna(x) and x != '' else [])
            if 'Resistance' in df.columns and isinstance(df['Resistance'].iloc[0], str):
                df['Resistance'] = df['Resistance'].apply(lambda x: ast.literal_eval(x) if pd.notna(x) and x != '' else [])
            
            self.data = df
            st.session_state.data = df
            return df
            
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")
            return None
    
    def filter_data_by_period(self, period):
        """Filter data based on selected time period"""
        if self.data is None:
            return None
        
        end_date = self.data['Date'].max()
        
        if period == '1D':
            start_date = end_date - timedelta(days=1)
        elif period == '1W':
            start_date = end_date - timedelta(weeks=1)
        elif period == '1M':
            start_date = end_date - timedelta(days=30)
        elif period == '3M':
            start_date = end_date - timedelta(days=90)
        elif period == '1Y':
            start_date = end_date - timedelta(days=365)
        elif period == '3Y':
            start_date = end_date - timedelta(days=1095)
        else:
            return self.data
        
        filtered_data = self.data[self.data['Date'] >= start_date]
        return filtered_data if len(filtered_data) > 0 else self.data.tail(10)
    
    def create_candlestick_chart(self, time_period='ALL', data=None, chart_key='chart'):
        """Create TradingView-style chart using lightweight-charts"""
        if data is None:
            if self.data is None:
                return None
            filtered_data = self.filter_data_by_period(time_period)
        else:
            filtered_data = data
            
        df = filtered_data.copy()

        # Convert datetime to string format
        df['time'] = df['Date'].dt.strftime('%Y-%m-%d')

        # Create candlestick series
        candles = df[['time', 'Open', 'High', 'Low', 'Close']].rename(columns={
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close'
        }).to_dict('records')

        # Create markers for signals
        markers = []
        for _, row in df.iterrows():
            direction = str(row['direction']).strip().upper()
            
            if direction == 'LONG':
                markers.append({
                    'time': row['time'],
                    'position': 'belowBar',
                    'color': '#00d4aa',
                    'shape': 'arrowUp',
                    'text': 'LONG'
                })
            elif direction == 'SHORT':
                markers.append({
                    'time': row['time'],
                    'position': 'aboveBar',
                    'color': '#ff4976',
                    'shape': 'arrowDown',
                    'text': 'SHORT'
                })
            else:
                markers.append({
                    'time': row['time'],
                    'position': 'inBar',
                    'color': '#FFD700',
                    'shape': 'text',
                    'text': 'N',
                    'size': 5
                })

        # Create support/resistance lines
        support_bands = []
        resistance_bands = []
        for idx, row in df.iterrows():
            # Support band (min to max of Support list)
            if isinstance(row['Support'], list) and len(row['Support']) > 0:
                support_min = min(row['Support'])
                support_max = max(row['Support'])
                support_bands.append({
                    'time': row['time'],
                    'value': support_min,
                    'value2': support_max
                })
            
            # Resistance band (min to max of Resistance list)
            if isinstance(row['Resistance'], list) and len(row['Resistance']) > 0:
                resistance_min = min(row['Resistance'])
                resistance_max = max(row['Resistance'])
                resistance_bands.append({
                    'time': row['time'],
                    'value': resistance_min,
                    'value2': resistance_max
                })

        # Chart configuration
        chartOptions = {
            "width": 1200,
            "height": 600,
            "layout": {
                "background": {
                    "type": "solid",
                    "color": "#0f0f23"
                },
                "textColor": "#d1d4dc"
            },
            "grid": {
                "vertLines": {
                    "color": "#2d3748"
                },
                "horzLines": {
                    "color": "#2d3748"
                }
            },
            "rightPriceScale": {
                "borderColor": "#2d3748",
                "scaleMargins": {
                    "top": 0.1,
                    "bottom": 0.1
                }
            },
            "timeScale": {
                "borderColor": "#2d3748",
                "timeVisible": True,
                "secondsVisible": False
            }
        }

        series = [
            {
                'type': 'Candlestick',
                'data': candles,
                'options': {
                    'upColor': '#00d4aa',
                    'downColor': '#ff4976',
                    'borderUpColor': '#00d4aa',
                    'borderDownColor': '#ff4976',
                    'wickUpColor': '#00d4aa',
                    'wickDownColor': '#ff4976',
                    'priceLineVisible': False,
                    'lastValueVisible': False,
                    'title': 'TSLA',
                    
                }
            },
            {
                'type': 'Area',
                'data': [{'time': d['time'], 'value': d['value'], 'value2': d['value2']} for d in support_bands],
                'options': {
                    'color': '#48bb7830',  # Green with 20% opacity
                    'title': 'Support Band',
                    'lineWidth': 0,
                    'priceLineVisible': False
                }
            },
            {
                'type': 'Area', 
                'data': [{'time': d['time'], 'value': d['value'], 'value2': d['value2']} for d in resistance_bands],
                'options': {
                    'color': '#f5656530',  # Red with 20% opacity
                    'title': 'Resistance Band',
                    'lineWidth': 0,
                    'priceLineVisible': False
                }
            }
        ]
            
        return renderLightweightCharts([{
            "chart": chartOptions,
            "series": series,
            "markers": markers
        }], chart_key)

    def get_data_summary(self, time_period='ALL'):
        """Get summary statistics of the data"""
        if self.data is None:
            return {}
        
        filtered_data = self.filter_data_by_period(time_period)
        
        summary = {
            'total_days': len(filtered_data),
            'long_signals': len(filtered_data[filtered_data['direction'] == 'LONG']),
            'short_signals': len(filtered_data[filtered_data['direction'] == 'SHORT']),
            'neutral_days': len(filtered_data[filtered_data['direction'] == 0]),
            'avg_price': filtered_data['Close'].mean(),
            'max_price': filtered_data['High'].max(),
            'min_price': filtered_data['Low'].min(),
            'total_volume': filtered_data['Volume'].sum(),
            'price_change': ((filtered_data['Close'].iloc[-1] - filtered_data['Close'].iloc[0]) / filtered_data['Close'].iloc[0]) * 100 if len(filtered_data) > 1 else 0
        }
        
        return summary
    
    def query_data_with_ai(self, question, time_period='ALL'):
        """Query data using Groq AI"""
        if self.data is None:
            return "Please load data first."
        
        try:
            filtered_data = self.filter_data_by_period(time_period)
            summary = self.get_data_summary(time_period)
            symbol_name = self.symbol if self.symbol else "Stock"
            data_context = f"""
            {symbol_name} Stock Data Summary for the {time_period} period:
            - Total trading days: {summary['total_days']}
            - Long signals: {summary['long_signals']}
            - Short signals: {summary['short_signals']}
            - Neutral days: {summary['neutral_days']}
            - Average closing price: ${summary['avg_price']:.2f}
            - Highest price: ${summary['max_price']:.2f}
            - Lowest price: ${summary['min_price']:.2f}
            - Total volume traded: {summary['total_volume']:,}
            - Overall price change: {summary['price_change']:.2f}%
            
            Date range for this period: {filtered_data['Date'].min().strftime('%Y-%m-%d')} to {filtered_data['Date'].max().strftime('%Y-%m-%d')}
            
            Sample data points:
            {filtered_data.head().to_string()}
            """
            
            prompt = f"""
            Based only on the following {symbol_name} stock data for the {time_period} period, please answer this question: {question}
            
            {data_context}
            
            Answer questions briefly and directly. Give only the requested value with a short label. No explanations unless asked.
            """
            
            if not self.groq_client:
                self.setup_groq()
            
            response = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"),
                temperature=0.3,
                max_tokens=1024,
            )
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error querying AI: {str(e)}"

def main():
    st.markdown('<h1 class="main-header">⚡ Professional Stock Trading Dashboard</h1>', unsafe_allow_html=True)
    
    dashboard = TSLADashboard()
    
    st.sidebar.title("Configuration")
    
    # Choose data source
    data_source = st.sidebar.radio(
        "Select Data Source:",
        ["Alpha Vantage API", "Upload CSV"],
        help="Choose where to get your stock data"
    )
    
    data_loaded = False
    api_key = os.getenv("ALPHAVANTAGE_API_KEY")
    
    if data_source == "Alpha Vantage API":
        if not api_key:
            st.sidebar.error("⚠️ Alpha Vantage API key not found in .env file. Please add ALPHAVANTAGE_API_KEY to your .env file.")
        else:
            symbol = st.sidebar.text_input(
                "Stock Symbol",
                value="TSLA",
                placeholder="e.g., AAPL, GOOGL, MSFT",
                help="Enter the stock ticker symbol"
            ).upper()
            
            if st.sidebar.button("📥 Fetch Data from API", use_container_width=True):
                if not symbol:
                    st.sidebar.error("⚠️ Please enter a stock symbol")
                else:
                    with st.spinner(f"Fetching {symbol} data from Alpha Vantage..."):
                        data = dashboard.load_data(symbol=symbol, api_key=api_key)
                        if data is not None:
                            st.session_state.data = data
                            st.sidebar.success(f"✅ {symbol} data loaded successfully!")
                            data_loaded = True
    else:
        uploaded_file = st.sidebar.file_uploader(
            "Upload Stock Data CSV",
            type=['csv'],
            help="Upload your stock data CSV file (must contain Date, Open, High, Low, Close, Volume columns)"
        )
        
        if uploaded_file is not None:
            with st.spinner("Loading data from CSV..."):
                data = dashboard.load_data(uploaded_file=uploaded_file)
                if data is not None:
                    st.session_state.data = data
                    st.sidebar.success("✅ Data loaded successfully!")
                    data_loaded = True
    
    # Use session data if available
    if st.session_state.data is not None:
        dashboard.data = st.session_state.data
    
    # Add third tab for replay feature
    tab1, tab2, tab3 = st.tabs(["📊 Trading Chart", "🤖 AI Analysis", "▶️ Replay Chart"])
    
    with tab1:
        if dashboard.data is not None:
            st.markdown(f"""
            <div class="chart-container">
                <div class="chart-header">
                    <h3 class="chart-title">{dashboard.symbol if dashboard.symbol else 'Stock'} • Stock Trading Chart</h3>
                </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3, col4, col5, col6, col7 = st.columns([1, 1, 1, 1, 1, 1, 4])
            
            with col1:
                if st.button("1D", key="1d_btn", use_container_width=True):
                    st.session_state.time_period = '1D'
            with col2:
                if st.button("1W", key="1w_btn", use_container_width=True):
                    st.session_state.time_period = '1W'
            with col3:
                if st.button("1M", key="1m_btn", use_container_width=True):
                    st.session_state.time_period = '1M'
            with col4:
                if st.button("3M", key="3m_btn", use_container_width=True):
                    st.session_state.time_period = '3M'
            with col5:
                if st.button("1Y", key="1y_btn", use_container_width=True):
                    st.session_state.time_period = '1Y'
            with col6:
                if st.button("ALL", key="all_btn", use_container_width=True):
                    st.session_state.time_period = 'ALL'
            
            st.info(f"📅 Currently viewing: **{st.session_state.time_period}** period")
            
            with st.spinner("Loading chart..."):
                chart = dashboard.create_candlestick_chart(st.session_state.time_period)
                if chart:
                    st.components.v1.html(chart, height=600)

            st.markdown("""
                <div class="legend-container">
                    <div class="legend-item">
                        <span class="legend-dot support"></span>
                        <span>Support Zones</span>
                    </div>
                    <div class="legend-item">
                        <span class="legend-dot resistance"></span>
                        <span>Resistance Zones</span>
                    </div>
                    <div class="legend-item">
                        <span class="legend-dot long"></span>
                        <span>LONG Signals</span>
                    </div>
                    <div class="legend-item">
                        <span class="legend-dot short"></span>
                        <span>SHORT Signals</span>
                    </div>
                    <div class="legend-item">
                        <span class="legend-dot neutral"></span>
                        <span>Neutral Signals</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            summary = dashboard.get_data_summary(st.session_state.time_period)
            
            st.markdown("### 📊 Market Overview")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Trading Days</div>
                    <div class="metric-value">{summary['total_days']}</div>
                    <div class="metric-delta">{st.session_state.time_period} Period</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                long_pct = (summary['long_signals']/summary['total_days']*100) if summary['total_days'] > 0 else 0
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Long Signals</div>
                    <div class="metric-value">{summary['long_signals']}</div>
                    <div class="metric-delta">{long_pct:.1f}% of days</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                short_pct = (summary['short_signals']/summary['total_days']*100) if summary['total_days'] > 0 else 0
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Short Signals</div>
                    <div class="metric-value">{summary['short_signals']}</div>
                    <div class="metric-delta">{short_pct:.1f}% of days</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                change_color = "#68d391" if summary['price_change'] >= 0 else "#f56565"
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Price Change</div>
                    <div class="metric-value" style="color: {change_color}">{summary['price_change']:.2f}%</div>
                    <div class="metric-delta">${summary['avg_price']:.2f} avg</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("### 📋 Recent Data")
            filtered_data = dashboard.filter_data_by_period(st.session_state.time_period)
            st.dataframe(
                filtered_data.head(20),
                use_container_width=True,
                height=400
            )
            
        else:
            st.markdown("""
            <div class="chart-container" style="text-align: center; padding: 60px;">
                <h3 style="color: #a0aec0; margin-bottom: 20px;">📊 No Data Available</h3>
                <p style="color: #68747f;">Select a data source in the sidebar and load your stock data to begin analysis</p>
            </div>
            """, unsafe_allow_html=True)
    
    with tab2:
        st.subheader("🤖 AI-Powered Data Analysis")
        
        if dashboard.data is None:
            st.warning("⚠️ Please load data first to use AI features")
        else:
            if dashboard.setup_groq():
                st.success("✅ AI Assistant ready!")
                
                st.subheader("💡 Sample Questions")
                sample_questions = [
                    "How many bullish days were in this period?",
                    "What was the highest closing price and when did it occur?",
                    "How many LONG vs SHORT signals were generated?",
                    "What was the average trading volume?",
                    "Which period had the most volatile price movements?",
                    "What percentage of days had neutral signals?",
                    "What was the biggest single-day price change?",
                    "How did the price perform overall in this period?"
                ]
                
                cols = st.columns(2)
                for i, question in enumerate(sample_questions):
                    col = cols[i % 2]
                    if col.button(question, key=f"sample_{i}"):
                        with st.spinner("🤔 AI is thinking..."):
                            response = dashboard.query_data_with_ai(question, st.session_state.time_period)
                            st.session_state.chat_history.append({"question": question, "answer": response})
                
                st.markdown("---")
                
                st.subheader("💬 Ask Your Question")
                user_question = st.text_input("Enter your question about the stock data:")
                
                if st.button("🚀 Ask AI", type="primary"):
                    if user_question:
                        with st.spinner("🤔 AI is analyzing..."):
                            response = dashboard.query_data_with_ai(user_question, st.session_state.time_period)
                            st.session_state.chat_history.append({"question": user_question, "answer": response})
                    else:
                        st.warning("Please enter a question first!")
                
                if st.session_state.chat_history:
                    st.markdown("---")
                    st.subheader("📝 Chat History")
                    
                    for i, chat in enumerate(reversed(st.session_state.chat_history)):
                        with st.expander(f"Q: {chat['question'][:100]}...", expanded=(i == 0)):
                            st.markdown(f"**Question:** {chat['question']}")
                            st.markdown(f"**Answer:** {chat['answer']}")
                
                if st.button("🗑️ Clear Chat History"):
                    st.session_state.chat_history = []
                    st.rerun()
                    
    # Add replay tab from app.py
    with tab3:
        st.subheader("▶️ Chart Replay")
        
        if dashboard.data is None:
            st.warning("⚠️ Please upload data first to use the replay feature")
        else:
            # Replay controls
            col1, col2, col3 = st.columns([1, 1, 2])
            
            with col1:
                replay_speed = st.select_slider(
                    "Replay Speed",
                    options=[0.5, 1, 2, 5, 10],
                    value=1,
                    help="Speed multiplier for the replay"
                )
            
            with col2:
                if 'replay_running' not in st.session_state:
                    st.session_state.replay_running = False
                
                if st.button("▶️ Start" if not st.session_state.replay_running else "⏸️ Pause"):
                    st.session_state.replay_running = not st.session_state.replay_running
                    st.rerun()
            
            with col3:
                if 'replay_index' not in st.session_state:
                    st.session_state.replay_index = 0
                
                if st.button("🔄 Reset"):
                    st.session_state.replay_index = 0
                    st.session_state.replay_running = False
                    st.rerun()
            
            # Create replay chart
            if st.session_state.replay_running:
                # Get data up to current replay index
                replay_data = dashboard.data.iloc[:st.session_state.replay_index + 1]
                
                # Create chart
                chart = dashboard.create_candlestick_chart('ALL', replay_data, chart_key="replay_chart")
                if chart:
                    st.components.v1.html(chart, height=600, key="replay_chart_container")
                
                # Update replay index
                if st.session_state.replay_index < len(dashboard.data) - 1:
                    st.session_state.replay_index += 1
                    time.sleep(1 / replay_speed)
                    st.rerun()
                else:
                    st.session_state.replay_running = False
                    st.rerun()
            else:
                # Show static chart up to current replay index
                replay_data = dashboard.data.iloc[:st.session_state.replay_index + 1]
                chart = dashboard.create_candlestick_chart('ALL', replay_data, chart_key="replay_chart_static")
                if chart:
                    st.components.v1.html(chart, height=600, key="replay_chart_static_container")
            
            # Show progress
            progress = (st.session_state.replay_index + 1) / len(dashboard.data) * 100
            st.progress(min(progress / 100, 1.0))
            st.text(f"Progress: {st.session_state.replay_index + 1} / {len(dashboard.data)} days")

if __name__ == "__main__":
    main()
