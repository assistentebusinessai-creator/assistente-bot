import os, re
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, ContextTypes,
    ConversationHandler, MessageHandler, filters
)

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # es: https://tuo-servizio.onrender.com/webhook

# ---- Stati conversazione /preventivo ----
NOME, SERVIZIO, DESCR, BUDGET, EMAIL = range(5)

# ---- App Telegram (stessi handler che usi in locale) ----
tg = Application.builder().token(BOT_TOKEN).build()

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ciao 👋 sono il tuo Assistente Business AI! Scrivi /preventivo per iniziare.")

async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Comandi disponibili:\n"
        "/start - Avvio\n"
        "/help - Aiuto\n"
        "/info - Info sul bot\n"
        "/preventivo - Crea un preventivo guidato\n"
        "/cancel - Annulla"
    )

async def info_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Assistente AI per micro-business: preventivi, contatti e bozze email 🚀")

async def preventivo_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Perfetto! ✍️ Come si chiama il *cliente*?")
    return NOME

async def ask_servizio(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["nome"] = update.message.text.strip()
    await update.message.reply_text("Qual è il *servizio* richiesto? (es. Logo, Sito web, Consulenza 1h)")
    return SERVIZIO

async def ask_descr(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["servizio"] = update.message.text.strip()
    await update.message.reply_text("Scrivi una *breve descrizione* (max 200 caratteri).")
    return DESCR

async def ask_budget(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["descr"] = update.message.text.strip()[:200]
    await update.message.reply_text("Qual è il *budget* indicativo (in €)?")
    return BUDGET

async def ask_email(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    testo = update.message.text.strip().replace(",", ".")
    try:
        budget = float(re.findall(r"\d+(?:\.\d+)?", testo)[0])
    except Exception:
        await update.message.reply_text("Inserisci un numero (es. 150 o 199.90). Quanto vuoi chiedere in €?")
        return BUDGET
    ctx.user_data["budget"] = budget
    await update.message.reply_text("Infine, scrivi l'*email del cliente* (es. nome@dominio.com)")
    return EMAIL

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

async def preventivo_done(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    email = update.message.text.strip()
    if not EMAIL_RE.match(email):
        await update.message.reply_text("Email non valida. Riprova (es. nome@dominio.com):")
        return EMAIL

    nome = ctx.user_data["nome"]
    serv = ctx.user_data["servizio"]
    descr = ctx.user_data["descr"]
    budget = ctx.user_data["budget"]

    msg = (
        "✅ *Preventivo creato*\n"
        f"• Cliente: *{nome}*\n"
        f"• Servizio: *{serv}*\n"
        f"• Descrizione: {descr}\n"
        f"• Budget: *€ {budget:,.2f}*\n"
        f"• Email: {email}\n\n"
        "_Online h24 via webhook su Render_"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")
    ctx.user_data.clear()
    return ConversationHandler.END

async def preventivo_cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    await update.message.reply_text("Procedura annullata 👍")
    return ConversationHandler.END

# Registra handler
tg.add_handler(CommandHandler("start", start))
tg.add_handler(CommandHandler("help", help_cmd))
tg.add_handler(CommandHandler("info", info_cmd))
conv = ConversationHandler(
    entry_points=[CommandHandler("preventivo", preventivo_start)],
    states={
        NOME:     [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_servizio)],
        SERVIZIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_descr)],
        DESCR:    [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_budget)],
        BUDGET:   [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_email)],
        EMAIL:    [MessageHandler(filters.TEXT & ~filters.COMMAND, preventivo_done)],
    },
    fallbacks=[CommandHandler("cancel", preventivo_cancel)],
)
tg.add_handler(conv)

# ---- FastAPI + webhook ----
app = FastAPI()

@app.get("/")
async def root():
    return {"ok": True, "msg": "Bot alive"}

@app.on_event("startup")
async def set_webhook():
    # imposta il webhook quando l'app si avvia
    if WEBHOOK_URL:
        await tg.bot.set_webhook(WEBHOOK_URL)

@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, tg.bot)
    await tg.process_update(update)
    return {"ok": True}
