# main.py
from fastapi import FastAPI, Request
import requests

app = FastAPI()

BINANCE_API_KEY = "TU_API_KEY"
BINANCE_SECRET = "TU_SECRET"

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    signal = data.get("message")
    
    if signal == "COMPRA":
        # Aquí colocas la orden de compra
        print("Señal de COMPRA recibida")
    elif signal == "VENTA":
        # Aquí colocas la orden de venta
        print("Señal de VENTA recibida")
    
    return {"status": "ok"}
