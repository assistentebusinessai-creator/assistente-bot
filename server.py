import os
from fastapi import FastAPI, Request
from telegram import Update
from main import build_application

WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")

app = FastAPI()
tg_app = build_application()

@app.on_event("startup")
async def on_startup():
    # Inizializza e avvia il bot, poi imposta il webhook
    await tg_app.initialize()
    if WEBHOOK_URL:
        await tg_app.bot.set_webhook(url=WEBHOOK_URL)
    await tg_app.start()

@app.on_event("shutdown")
async def on_shutdown():
    await tg_app.stop()
    await tg_app.shutdown()

@app.get("/")
async def root():
    return {"ok": True, "msg": "Bot alive"}

@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, tg_app.bot)
    await tg_app.process_update(update)
    return {"ok": True}

