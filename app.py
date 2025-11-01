import streamlit as st
import yfinance as yf
import pandas as pd
import time

# 🌙 Configuración de la app
st.set_page_config(page_title="Analizador Bolsa USA", page_icon="💹", layout="wide")

st.title("💹 Analizador de Bolsa USA y Criptomonedas")
st.markdown("Visualiza precios en tiempo real, tendencias y señales de compra o venta.")

# 🏢 Lista de empresas y criptos
opciones = {
    "Acciones": ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "JPM", "V", "WMT"],
    "Criptomonedas": ["BTC-USD", "ETH-USD", "DOGE-USD", "SOL-USD"]
}

# 🎯 Selección múltiple
st.sidebar.header("Configuración")
seleccion = st.sidebar.multiselect(
    "Elige empresas o criptos:",
    opciones["Acciones"] + opciones["Criptomonedas"],
    default=["AAPL", "BTC-USD"]
)

intervalo = st.sidebar.slider("⏱️ Intervalo de actualización (segundos)", 5, 120, 30)

# 📈 Función para obtener datos
def obtener_datos(simbolo):
    try:
        data = yf.download(simbolo, period="5d", interval="1h")
        if data.empty:
            st.warning(f"No hay datos disponibles para {simbolo}.")
            return None
        data["RSI"] = calcular_RSI(data["Close"])
        data["MA20"] = data["Close"].rolling(window=20).mean()
        return data
    except Exception as e:
        st.error(f"Error al obtener datos de {simbolo}: {e}")
        return None

# 📊 RSI (Índice de Fuerza Relativa)
def calcular_RSI(series, periodo=14):
    delta = series.diff()
    ganancia = delta.where(delta > 0, 0)
    perdida = -delta.where(delta < 0, 0)
    promedio_gan = ganancia.rolling(periodo).mean()
    promedio_perd = perdida.rolling(periodo).mean()
    rs = promedio_gan / promedio_perd
    return 100 - (100 / (1 + rs))

# 🚦 Señales de compra/venta
def generar_senal(data):
    if data is None or len(data) < 20:
        return "⚪ Sin datos"
    rsi = data["RSI"].iloc[-1]
    close = data["Close"].iloc[-1]
    ma20 = data["MA20"].iloc[-1]
    if rsi < 30 and close > ma20:
        return "🟢 Compra"
    elif rsi > 70 and close < ma20:
        return "🔴 Venta"
    else:
        return "⚪ Mantener"

# 🔁 Actualización automática
while True:
    for simbolo in seleccion:
        st.subheader(f"{simbolo}")
        data = obtener_datos(simbolo)
        for simbolo in seleccion:
    st.subheader(f"{simbolo}")
    data = obtener_datos(simbolo)

    if data is not None and not data.empty:
        precio = data["Close"].iloc[-1]
        apertura = data["Open"].iloc[-1]
        variacion = ((precio - apertura) / apertura) * 100
        senal = generar_senal(data)

        st.write(f"💰 **Precio actual:** ${precio:.2f}")
        st.write(f"📊 **Variación del día:** {variacion:.2f}%")
        st.write(f"📈 **Señal:** {senal}")

        st.line_chart(data["Close"])
    else:
        st.warning(f"⚠️ No se pudieron obtener datos para {simbolo}.")

    st.markdown("---")

st.info(f"⏳ Actualizando datos cada {intervalo} segundos...")
time.sleep(intervalo)
st.rerun()
