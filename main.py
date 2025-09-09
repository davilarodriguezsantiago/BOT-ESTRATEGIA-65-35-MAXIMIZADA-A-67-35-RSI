from fastapi import FastAPI, Request
from binance.client import Client
from binance.enums import *
import sqlite3
import os

# ======================
# Configuración
# ======================
API_KEY = os.getenv("BINANCE_KEY")
API_SECRET = os.getenv("BINANCE_SECRET")
SYMBOL = "BTCUSDT"
CAPITAL_INICIAL = 15.0  # USDT de inicio

client = Client(API_KEY, API_SECRET)
app = FastAPI()

# ======================
# Base de datos SQLite
# ======================
def init_db():
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS estado (
        id INTEGER PRIMARY KEY,
        capital REAL,
        ultima_orden TEXT,
        precio REAL,
        cantidad REAL
    )
    """)
    # Insertar capital inicial si está vacío
    cursor.execute("SELECT COUNT(*) FROM estado")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO estado (capital, ultima_orden, precio, cantidad) VALUES (?, ?, ?, ?)",
                       (CAPITAL_INICIAL, None, 0, 0))
    conn.commit()
    conn.close()

def get_estado():
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT capital, ultima_orden, precio, cantidad FROM estado WHERE id = 1")
    row = cursor.fetchone()
    conn.close()
    return {"capital": row[0], "ultima_orden": row[1], "precio": row[2], "cantidad": row[3]}

def update_estado(capital, ultima_orden, precio, cantidad):
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE estado SET capital=?, ultima_orden=?, precio=?, cantidad=? WHERE id=1
    """, (capital, ultima_orden, precio, cantidad))
    conn.commit()
    conn.close()

# Inicializar DB
init_db()

# ======================
# Endpoints
# ======================
@app.get("/")
def home():
    estado = get_estado()
    return {"status": "bot funcionando", "capital": estado["capital"]}

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    signal = data.get("message")
    estado = get_estado()

    capital = estado["capital"]
    ultima_orden = estado["ultima_orden"]
    precio_entrada = estado["precio"]
    cantidad = estado["cantidad"]

    # Señal de COMPRA
    if signal == "COMPRA" and (ultima_orden is None or ultima_orden == "VENTA"):
        precio = float(client.get_symbol_ticker(symbol=SYMBOL)["price"])
        cantidad = round(capital / precio, 6)

        orden = client.create_order(
            symbol=SYMBOL,
            side=SIDE_BUY,
            type=ORDER_TYPE_MARKET,
            quantity=cantidad
        )

        update_estado(capital, "COMPRA", precio, cantidad)
        return {"status": "ok", "accion": "COMPRA", "precio": precio, "cantidad": cantidad, "capital": capital}

    # Señal de VENTA
    elif signal == "VENTA" and ultima_orden == "COMPRA":
        precio = float(client.get_symbol_ticker(symbol=SYMBOL)["price"])

        orden = client.create_order(
            symbol=SYMBOL,
            side=SIDE_SELL,
            type=ORDER_TYPE_MARKET,
            quantity=cantidad
        )

        # Calcular ganancia/pérdida
        entrada = precio_entrada * cantidad
        salida = precio * cantidad
        ganancia = salida - entrada
        capital += ganancia

        update_estado(capital, "VENTA", precio, 0)
        return {"status": "ok", "accion": "VENTA", "precio": precio, "ganancia": ganancia, "capital": capital}

    return {"status": "sin acción"}
