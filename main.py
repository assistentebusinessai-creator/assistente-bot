import os
import re
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, ContextTypes,
    ConversationHandler, MessageHandler, filters
)

# ===== Config =====
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Stati conversazione
NOME, SERVIZIO, DESCR, BUDGET, EMAIL = range(5)

# ===== Comandi base =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ciao 👋 sono il tuo Assistente Business AI! Scrivi /preventivo per crearne uno guidato.")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Comandi disponibili:\n"
        "/start - Avvio\n"
        "/help - Aiuto\n"
        "/info - Info sul bot\n"
        "/preventivo - Crea un preventivo guidato\n"
        "/cancel - Annulla la procedura in corso"
    )

async def info_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Assistente AI per micro-business: preventivi, contatti, bozze email 🚀")

# ===== /preventivo (conversazione) =====
async def preventivo_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Perfetto! ✍️ Come si chiama il *cliente*?")
    return NOME

async def ask_servizio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["nome"] = update.message.text.strip()
    await update.message.reply_text("Qual è il *servizio* richiesto? (es. Logo, Sito web, Consulenza 1h)")
    return SERVIZIO

async def ask_descr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["servizio"] = update.message.text.strip()
    await update.message.reply_text("Scrivi una *breve descrizione* del lavoro (max 200 caratteri).")
    return DESCR

async def ask_budget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["descr"] = update.message.text.strip()[:200]
    await update.message.reply_text("Qual è il *budget* indicativo (in €)?")
    return BUDGET

async def ask_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    testo = update.message.text.strip().replace(",", ".")
    # prova a prendere un numero (intero/decimale)
    try:
        budget = float(re.findall(r"\d+(?:\.\d+)?", testo)[0])
    except Exception:
        await update.message.reply_text("Per favore inserisci un numero (es. 150 o 199.90). Quanto vuoi chiedere in €?")
        return BUDGET

    context.user_data["budget"] = budget
    await update.message.reply_text("Infine, scrivi l'*email del cliente* (es. nome@dominio.com)")
    return EMAIL

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

async def preventivo_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text.strip()
    if not EMAIL_RE.match(email):
        await update.message.reply_text("Mmm, quell'email non sembra valida. Riprova (es. nome@dominio.com):")
        return EMAIL

    context.user_data["email"] = email

    nome = context.user_data["nome"]
    serv = context.user_data["servizio"]
    descr = context.user_data["descr"]
    budget = context.user_data["budget"]

    msg = (
        "✅ *Preventivo creato*\n"
        f"• Cliente: *{nome}*\n"
        f"• Servizio: *{serv}*\n"
        f"• Descrizione: {descr}\n"
        f"• Budget: *€ {budget:,.2f}*\n"
        f"• Email: {email}\n\n"
        "_Prossimi step (Giorno 3): salvataggio su Google Sheets + bozza email automatica_"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

    context.user_data.clear()
    return ConversationHandler.END

async def preventivo_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Procedura annullata 👍")
    return ConversationHandler.END

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Comandi base
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("info", info_cmd))

    # Conversazione preventivo
    conv = ConversationHandler(
        entry_points=[CommandHandler("preventivo", preventivo_start)],
        states={
            NOME:    [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_servizio)],
            SERVIZIO:[MessageHandler(filters.TEXT & ~filters.COMMAND, ask_descr)],
            DESCR:   [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_budget)],
            BUDGET:  [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_email)],
            EMAIL:   [MessageHandler(filters.TEXT & ~filters.COMMAND, preventivo_done)],
        },
        fallbacks=[CommandHandler("cancel", preventivo_cancel)],
    )
    app.add_handler(conv)

    app.run_polling()

if __name__ == "__main__":
    main()


