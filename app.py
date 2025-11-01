# app.py
# Analizador Bolsa USA Pro - versión web (tema oscuro, en español)
# Ejecutar localmente: streamlit run app.py
# Requiere: streamlit, yfinance, pandas, numpy, matplotlib

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

st.set_page_config(page_title="Analizador Bolsa USA Pro", layout="wide", initial_sidebar_state="expanded")

# ----- Estilo oscuro -----
st.markdown(
    """
    <style>
    .reportview-container, .main, header, .stApp {
        background-color: #0b0f13;
        color: #d6d6d6;
    }
    .stButton>button { background-color:#0b1220; color:#d6d6d6; }
    .stMetric { color:#d6d6d6; }
    .css-1d391kg { background-color: #071018; } /* sidebar */
    </style>
    """, unsafe_allow_html=True
)

st.title("📊 Analizador Bolsa USA Pro (EN VIVO)")
st.markdown("Interfaz en español — tema oscuro. Datos en vivo para acciones y criptomonedas (via Yahoo Finance). Señales básicas: SMA crossover + RSI. **No es asesoría financiera.**")

# ----- Valores por defecto (14 items) -----
DEFAULT_TICKERS = [
    "AAPL","MSFT","AMZN","NVDA","GOOGL","META","TSLA","BRK-B",
    "BTC-USD","ETH-USD","SOL-USD","DOGE-USD","ADA-USD","XRP-USD"
]

# ----- Sidebar: configuración -----
st.sidebar.header("Configuración")
tickers_text = st.sidebar.text_area("Lista de tickers (separados por coma). Ejemplo: AAPL,MSFT,BTC-USD",
                                   value=",".join(DEFAULT_TICKERS), height=140)
tickers = [t.strip().upper() for t in tickers_text.split(",") if t.strip()!=""]

period = st.sidebar.selectbox("Periodo de datos", ["5d","1mo","3mo","6mo","1y","2y","5y"], index=4)
interval = st.sidebar.selectbox("Intervalo (granularidad)", ["1m","2m","5m","15m","30m","60m","1d","1wk"], index=6)

sma_short = st.sidebar.number_input("SMA corta (periodos)", min_value=1, max_value=200, value=20)
sma_long = st.sidebar.number_input("SMA larga (periodos)", min_value=2, max_value=400, value=50)
rsi_period = st.sidebar.number_input("RSI periodo", min_value=5, max_value=30, value=14)

auto_update = st.sidebar.checkbox("Auto-actualizar (recarga automática)", value=False)
update_seconds = st.sidebar.selectbox("Intervalo auto (segundos)", [10,20,30,60,120,300], index=2)
manual_refresh = st.sidebar.button("Actualizar ahora")

st.sidebar.markdown("---")
st.sidebar.markdown("Hecho por: Analizador Bolsa USA Pro - Interfaz en español\n\nNota: los datos provienen de Yahoo Finance y pueden tener ligeros retrasos para algunos tickers.")

# ----- Auto-refresh: inyectar JS para recarga cuando está activo -----
if auto_update:
    js = f"<script>setTimeout(()=>{{window.location.reload();}}, {int(update_seconds)*1000});</script>"
    st.components.v1.html(js, height=0)

# ----- Utilities -----
@st.cache_data(ttl=60)
def fetch_ticker(ticker, period, interval):
    try:
        df = yf.download(ticker, period=period, interval=interval, progress=False, threads=False)
        if df is None or df.empty:
            return None
        df = df.dropna()
        df.columns = [c.lower() for c in df.columns]
        df['close'] = df['close']
        return df
    except Exception:
        return None

def compute_indicators(df, sma_short, sma_long, rsi_period):
    df = df.copy()
    df['sma_short'] = df['close'].rolling(sma_short).mean()
    df['sma_long'] = df['close'].rolling(sma_long).mean()
    delta = df['close'].diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    ma_up = up.rolling(rsi_period).mean()
    ma_down = down.rolling(rsi_period).mean()
    rs = ma_up / ma_down
    df['rsi'] = 100 - (100 / (1 + rs))
    df['sma_pos'] = 0
    df.loc[df['sma_short'] > df['sma_long'], 'sma_pos'] = 1
    df['sma_cross'] = df['sma_pos'].diff()
    return df

def generate_signal(latest_row, rsi_oversold=30, rsi_overbought=70):
    sig = "Mantener"
    try:
        if latest_row.get('sma_cross', 0) == 1 or latest_row.get('rsi', 100) < rsi_oversold:
            sig = "Comprar"
        elif latest_row.get('sma_cross', 0) == -1 or latest_row.get('rsi', 0) > rsi_overbought:
            sig = "Vender"
    except Exception:
        sig = "Mantener"
    return sig

# ----- Main dashboard: grid de tickers -----
st.subheader("Tablero en vivo")
cols = st.columns(4)
statuses = {}
for i, t in enumerate(tickers):
    with cols[i % 4]:
        st.markdown(f"### {t}")
        df = fetch_ticker(t, period, interval)
        if df is None or df.empty:
            st.write("Datos no disponibles")
            statuses[t] = {"signal":"N/A"}
            continue
        df = compute_indicators(df, sma_short, sma_long, rsi_period)
        latest = df.iloc[-1]
        prev_close = df['close'].iloc[-2] if len(df) > 1 else latest['close']
        change_pct = (latest['close'] - prev_close) / prev_close * 100 if prev_close!=0 else 0.0
        signal = generate_signal(latest)
        st.metric(label="Último precio (USD)", value=f"{latest['close']:.2f}", delta=f"{change_pct:.2f}%")
        st.markdown(f"Señal: **{signal}**  \nRSI: {latest['rsi']:.1f}")
        statuses[t] = {"signal": signal, "price": latest['close'], "change": change_pct}

st.markdown("---")

# ----- Vista detallada -----
st.subheader("Ver detalle por ticker")
left, right = st.columns([1,2])
with left:
    selected = st.multiselect("Selecciona tickers para ver en detalle (puedes elegir varios)", options=tickers, default=[tickers[0]] if tickers else [])
    max_points = st.slider("Máximo de puntos a mostrar en gráfico", min_value=50, max_value=2000, value=500, step=50)
    show_csv = st.checkbox("Mostrar botón para descargar CSV", value=True)
with right:
    if not selected:
        st.info("Selecciona al menos un ticker para ver detalles.")
    else:
        for t in selected:
            st.markdown(f"## {t}")
            df = fetch_ticker(t, period, interval)
            if df is None or df.empty:
                st.error("Datos no disponibles")
                continue
            df = compute_indicators(df, sma_short, sma_long, rsi_period)
            latest = df.iloc[-1]
            prev_close = df['close'].iloc[-2] if len(df)>1 else latest['close']
            st.metric("Último precio (USD)", f"{latest['close']:.2f}", delta=f"{(latest['close']-prev_close)/prev_close*100:.2f}%")
            st.write(f"Señal actual: **{generate_signal(latest)}**  \nRSI: {latest['rsi']:.1f}")
            # Plot
            fig, ax = plt.subplots(2,1, figsize=(8,4), sharex=True)
            ax[0].plot(df.index[-max_points:], df['close'][-max_points:], label="Precio cierre")
            ax[0].plot(df.index[-max_points:], df['sma_short'][-max_points:], label=f"SMA {sma_short}")
            ax[0].plot(df.index[-max_points:], df['sma_long'][-max_points:], label=f"SMA {sma_long}")
            ax[0].legend(loc='upper left')
            ax[0].set_ylabel("USD")
            ax[1].plot(df.index[-max_points:], df['rsi'][-max_points:], label="RSI")
            ax[1].axhline(30, linestyle='--', alpha=0.5)
            ax[1].axhline(70, linestyle='--', alpha=0.5)
            ax[1].set_ylim(0,100)
            ax[1].legend()
            st.pyplot(fig)
            if show_csv:
                csv = df.to_csv().encode('utf-8')
                st.download_button(f"Descargar CSV {t}", data=csv, file_name=f"{t}_data.csv", mime="text/csv")

st.markdown("---")
st.markdown("Gestión: edita la lista de tickers en la barra lateral y pulsa 'Actualizar ahora' para recargar.")
st.caption("Nota: datos provistos por Yahoo Finance. Las señales son educativas y no constituyen asesoramiento financiero.")
