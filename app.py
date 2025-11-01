import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import time

st.set_page_config(page_title="Analizador Bolsa USA", layout="wide", page_icon="💹")

st.title("💹 Analizador Bolsa USA — en tiempo real")
st.markdown("### Señales automáticas de **COMPRA / VENTA** basadas en medias móviles y RSI")

# --- Barra lateral ---
st.sidebar.header("⚙️ Configuración")
intervalo = st.sidebar.selectbox("Intervalo de actualización", ["1m", "5m", "15m", "30m", "1h", "1d"], index=2)
actualizar = st.sidebar.slider("⏱️ Actualizar cada (segundos):", 10, 300, 60, step=10)

# --- Lista de símbolos ---
st.sidebar.subheader("📈 Selecciona empresas o criptomonedas")
opciones = {
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "GOOGL": "Google",
    "AMZN": "Amazon",
    "TSLA": "Tesla",
    "META": "Meta",
    "NVDA": "NVIDIA",
    "BTC-USD": "Bitcoin",
    "ETH-USD": "Ethereum",
    "DOGE-USD": "Dogecoin"
}
seleccion = st.sidebar.multiselect("Activos a analizar", options=list(opciones.keys()), default=["AAPL", "TSLA", "BTC-USD"])

# --- Función para RSI ---
def calcular_RSI(data, periodos=14):
    delta = data["Close"].diff()
    ganancia = delta.where(delta > 0, 0)
    perdida = -delta.where(delta < 0, 0)
    media_ganancia = ganancia.rolling(periodos).mean()
    media_perdida = perdida.rolling(periodos).mean()
    RS = media_ganancia / media_perdida
    RSI = 100 - (100 / (1 + RS))
    return RSI

# --- Análisis de cada activo ---
for simbolo in seleccion:
    try:
        data = yf.download(simbolo, period="5d", interval=intervalo, progress=False)
        data["MA20"] = data["Close"].rolling(20).mean()
        data["MA50"] = data["Close"].rolling(50).mean()
        data["RSI"] = calcular_RSI(data)

        precio = data["Close"].iloc[-1]
        ma20 = data["MA20"].iloc[-1]
        ma50 = data["MA50"].iloc[-1]
        rsi = data["RSI"].iloc[-1]

        # Señales de compra/venta combinadas
        if ma20 > ma50 and rsi < 60:
            señal = "🟢 COMPRA"
            color = "green"
        elif ma20 < ma50 and rsi > 50:
            señal = "🔴 VENTA"
            color = "red"
        else:
            señal = "⚪ NEUTRAL"
            color = "gray"

        st.markdown(f"## {opciones[simbolo]} ({simbolo})")
        st.markdown(f"💰 **Precio actual:** ${precio:,.2f}")
        st.markdown(f"📊 **MA20:** {ma20:,.2f} | **MA50:** {ma50:,.2f}")
        st.markdown(f"📉 **RSI:** {rsi:.2f}")
        st.markdown(f"### <span style='color:{color}'>{señal}</span>", unsafe_allow_html=True)
        st.line_chart(data[["Close", "MA20", "MA50"]])

        st.divider()
    except Exception as e:
        st.warning(f"⚠️ No se pudieron obtener datos de {simbolo}: {e}")

# --- Auto-actualización ---
st.toast("🔄 Los datos se actualizarán automáticamente")
time.sleep(actualizar)
st.rerun()
