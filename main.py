import os
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ConversationHandler,
    ContextTypes, filters
)

# Prende il token dalle variabili d'ambiente (Render -> Environment)
BOT_TOKEN = os.getenv("BOT_TOKEN")

# --- Comandi base ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Ciao 👋 sono l’assistente dell’officina!\n"
        "Comandi utili:\n"
        "• /preventivo – Richiedi un preventivo guidato\n"
        "• /costi – Prezzi indicativi\n"
        "• /orari – Orari e indirizzo\n"
        "• /help – Aiuto"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Comandi disponibili:\n"
        "/start /help /preventivo /costi /orari /cancel"
    )

# --- Conversazione /preventivo ---
NOME, TELEFONO, TARGA, PROBLEMA, URGENZA, FOTO = range(6)

async def preventivo_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Perfetto! Come ti chiami?")
    return NOME

async def preventivo_nome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["nome"] = update.message.text.strip()
    await update.message.reply_text("Il tuo numero di telefono?")
    return TELEFONO

async def preventivo_tel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["telefono"] = update.message.text.strip()
    await update.message.reply_text("Targa e modello dell’auto?")
    return TARGA

async def preventivo_targa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["targa"] = update.message.text.strip()
    await update.message.reply_text("Descrivi brevemente il problema.")
    return PROBLEMA

async def preventivo_problema(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["problema"] = update.message.text.strip()
    kb = ReplyKeyboardMarkup([["Bassa", "Media", "Alta"]], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("Urgenza?", reply_markup=kb)
    return URGENZA

async def preventivo_urgenza(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["urgenza"] = update.message.text.strip()
    await update.message.reply_text(
        "Se vuoi, invia una *foto* del problema oppure scrivi *salta*.",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    return FOTO

async def preventivo_foto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    foto_url = ""
    if update.message.photo:
        file = await update.message.photo[-1].get_file()
        foto_url = file.file_path
    elif update.message.text and update.message.text.lower().strip() == "salta":
        pass
    else:
        await update.message.reply_text("Invia una foto oppure scrivi 'salta'.")
        return FOTO

    context.user_data["foto"] = foto_url
    d = context.user_data
    riepilogo = (
        "✅ *Richiesta registrata*\n"
        f"• Nome: {d.get('nome','')}\n"
        f"• Tel: {d.get('telefono','')}\n"
        f"• Targa/Modello: {d.get('targa','')}\n"
        f"• Problema: {d.get('problema','')}\n"
        f"• Urgenza: {d.get('urgenza','')}\n"
        f"• Foto: {('allegata' if d.get('foto') else '—')}\n"
        f"• Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    )
    await update.message.reply_text(riepilogo, parse_mode="Markdown")
    return ConversationHandler.END

async def preventivo_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Operazione annullata.")
    return ConversationHandler.END

# --- FAQ ---
async def costi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💰 *Indicazioni di massima*\n"
        "- Tagliando base: da 120€\n"
        "- Cambio gomme: da 50€\n"
        "- Diagnosi elettronica: da 30€\n"
        "_Prezzi indicativi: preventivo definitivo dopo verifica in officina._",
        parse_mode="Markdown"
    )

async def orari(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⏰ Orari: Lun–Ven 8:30–12:30 / 14:00–18:00\n"
        "📍 Indirizzo: Via Esempio 10, Città\n"
        "📞 Telefono: 333 0000000"
    )

# --- Costruzione app PTB ---
def build_application() -> Application:
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN mancante nelle variabili d'ambiente")
    app = Application.builder().token(BOT_TOKEN).build()

    # Conversazione preventivo
    conv = ConversationHandler(
        entry_points=[CommandHandler("preventivo", preventivo_start)],
        states={
            NOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, preventivo_nome)],
            TELEFONO: [MessageHandler(filters.TEXT & ~filters.COMMAND, preventivo_tel)],
            TARGA: [MessageHandler(filters.TEXT & ~filters.COMMAND, preventivo_targa)],
            PROBLEMA: [MessageHandler(filters.TEXT & ~filters.COMMAND, preventivo_problema)],
            URGENZA: [MessageHandler(filters.TEXT & ~filters.COMMAND, preventivo_urgenza)],
            FOTO: [
                MessageHandler(filters.PHOTO, preventivo_foto),
                MessageHandler(filters.Regex("(?i)^salta$"), preventivo_foto),
                MessageHandler(filters.TEXT & ~filters.COMMAND, preventivo_foto),
            ],
        },
        fallbacks=[CommandHandler("cancel", preventivo_cancel)],
    )
    app.add_handler(conv)

    # Comandi base / FAQ
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("costi", costi))
    app.add_handler(CommandHandler("orari", orari))
    return app

# Solo per test locale con polling (non usato su Render)
if __name__ == "__main__":
    application = build_application()
    application.run_polling()





