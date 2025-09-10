import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ContextTypes, ConversationHandler, filters
)

# .env solo in locale; su Render usa le env vars della dashboard
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Stati della conversazione /preventivo
NOME, SERVIZIO, DESCR, BUDGET, EMAIL = range(5)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ciao 👋 sono il tuo Assistente Business AI!")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Comandi disponibili:\n/start - Avvio\n/help - Aiuto\n/info - Info sul bot\n/preventivo - Crea un preventivo")

async def info_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Sono un assistente AI che ti aiuta a gestire il tuo business.\n"
        "Posso organizzare richieste, generare preventivi, salvare contatti e creare bozze email 🚀"
    )

# ---- Conversazione preventivo ----
async def preventivo_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Perfetto! 👌 Qual è il *nome del cliente*?")
    return NOME

async def ask_servizio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["nome"] = update.message.text.strip()
    await update.message.reply_text("Che *servizio* richiede?")
    return SERVIZIO

async def ask_descr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["servizio"] = update.message.text.strip()
    await update.message.reply_text("Dammi una *breve descrizione* del lavoro:")
    return DESCR

async def ask_budget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["descr"] = update.message.text.strip()
    await update.message.reply_text("Qual è il *budget* (in €)?")
    return BUDGET

async def ask_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["budget"] = update.message.text.strip()
    await update.message.reply_text("Infine, l’*email del cliente* (es. nome@dominio.com)")
    return EMAIL

async def preventivo_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["email"] = update.message.text.strip()
    d = context.user_data
    testo = (
        "✅ *Preventivo creato*\n"
        f"• Cliente: {d['nome']}\n"
        f"• Servizio: {d['servizio']}\n"
        f"• Descrizione: {d['descr']}\n"
        f"• Budget: € {d['budget']}\n"
        f"• Email: {d['email']}\n"
    )
    await update.message.reply_text(testo, parse_mode="Markdown")
    return ConversationHandler.END

async def preventivo_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Operazione annullata.")
    return ConversationHandler.END
# -----------------------------------

def build_application() -> Application:
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("info", info_cmd))

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
    app.add_handler(conv)
    return app

# Permette di testare in locale con /polling (non su Render)
if __name__ == "__main__":
    application = build_application()
    application.run_polling()



