import streamlit as st
import yfinance as yf
import pandas as pd
import datetime as dt
import time

st.set_page_config(page_title="📈 Analizador Bolsa USA PRO", layout="wide")

st.title("📊 Analizador Bolsa USA PRO - En tiempo real")

# Fondo oscuro
st.markdown("""
    <style>
        body { background-color: #0e1117; color: #fafafa; }
        .stApp { background-color: #0e1117; }
    </style>
""", unsafe_allow_html=True)

# --- CONFIGURACIÓN ---
empresas = {
    "Apple (AAPL)": "AAPL",
    "Microsoft (MSFT)": "MSFT",
    "Tesla (TSLA)": "TSLA",
    "Amazon (AMZN)": "AMZN",
    "Nvidia (NVDA)": "NVDA",
    "Meta (META)": "META",
    "Alphabet (GOOGL)": "GOOGL",
    "Bitcoin (BTC-USD)": "BTC-USD",
    "Ethereum (ETH-USD)": "ETH-USD",
    "Dogecoin (DOGE-USD)": "DOGE-USD"
}

st.sidebar.header("⚙️ Configuración")

# Permitir agregar o quitar
nuevo = st.sidebar.text_input("Agregar símbolo (ej: NFLX o SOL-USD)")
if nuevo:
    empresas[nuevo] = nuevo

eliminar = st.sidebar.multiselect("Eliminar activos:", list(empresas.keys()))
for e in eliminar:
    empresas.pop(e, None)

seleccion = st.sidebar.multiselect(
    "Seleccionar activos a visualizar:",
    list(empresas.keys()),
    default=list(empresas.keys())
)

intervalo = st.sidebar.selectbox(
    "⏱️ Intervalo de actualización",
    ["1m", "5m", "15m", "30m", "1h"],
    index=2
)

actualizar_manual = st.sidebar.button("🔄 Actualizar ahora")

st.sidebar.info("Los datos se actualizan automáticamente o al presionar 'Actualizar ahora'.")

# --- FUNCIÓN PARA DESCARGAR DATOS ---
def obtener_datos(simbolo):
    try:
        data = yf.download(simbolo, period="1d", interval=intervalo, progress=False)
        return data
    except Exception as e:
        st.error(f"Error al obtener datos de {simbolo}: {e}")
        return pd.DataFrame()

# --- MOSTRAR DATOS ---
if st.button("🚀 Cargar datos") or actualizar_manual:
    for nombre, simbolo in empresas.items():
        if nombre in seleccion:
            data = obtener_datos(simbolo)
            if data.empty:
                st.warning(f"No hay datos disponibles para {nombre}.")
            else:
                precio = data["Close"].iloc[-1]
                variacion = (data["Close"].iloc[-1] - data["Close"].iloc[0]) / data["Close"].iloc[0] * 100
                st.subheader(f"{nombre} ({simbolo})")
                st.line_chart(data["Close"])
                st.write(f"💰 **Precio actual:** ${precio:.2f} | 📊 **Variación del día:** {variacion:.2f}%")

    st.success("Datos actualizados correctamente ✅")
else:
    st.info("Presiona el botón 🚀 'Cargar datos' para comenzar.")
