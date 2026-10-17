import os
import logging
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

def get_dynamic_sample_matches():
    """
    Δημιουργεί δυναμικά αγώνες με βάση την τρέχουσα ώρα του συστήματος,
    ώστε να ταιριάζουν πάντα απόλυτα με την πραγματική ώρα (π.χ. Ελλάδας).
    """
    now = datetime.now()
    
    # Ορίζουμε αγώνες με κλιμακωτές ώρες από τώρα και στο εξής
    t1 = (now + timedelta(minutes=15)).strftime("%H:%M")
    t2 = (now + timedelta(minutes=75)).strftime("%H:%M")
    t3 = (now + timedelta(minutes=135)).strftime("%H:%M")
    t4 = (now + timedelta(minutes=195)).strftime("%H:%M")
    t5 = (now + timedelta(minutes=255)).strftime("%H:%M")

    return [
        {"time": t1, "league": "⚽ Αγγλία - Premier League", "match": "Άρσεναλ VS Τσέλσι", "status": "NS"},
        {"time": t2, "league": "⚽ Ισπανία - La Liga", "match": "Μπαρτσελόνα VS Σεβίλλη", "status": "NS"},
        {"time": t3, "league": "⚽ Ιταλία - Serie A", "match": "Μίλαν VS Ίντερ", "status": "NS"},
        {"time": t4, "league": "⚽ Γαλλία - Ligue 1", "match": "Λιόν VS Μαρσέιγ", "status": "NS"},
        {"time": t5, "league": "⚽ Ελλάδα - Stoiximan Super League", "match": "Ολυμπιακός VS Παναθηναϊκός", "status": "NS"}
    ]

def format_matches_message():
    matches_list = get_dynamic_sample_matches()
    
    current_time_str = datetime.now().strftime("%H:%M")
    msg = f"📊 **ΣΗΜΕΡΙΝΟ ΠΡΟΓΡΑΜΜΑ & LIVE SCORE**\n"
    msg += f"🕒 Τρέχουσα Ώρα: `{current_time_str}`\n"
    msg += "----------------------------------------\n\n"
    
    for m in matches_list:
        msg += f"⏰ `{m['time']}` | {m['league']}\n"
        msg += f"🔥 **{m['match']}** [Status: `{m['status']}`]\n"
        msg += "----------------------------------------\n"

    msg += "\n🔄 *Πατήστε ανανέωση για ενημέρωση.*"
    return msg

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = format_matches_message()
    keyboard = [[InlineKeyboardButton("🔄 Ανανέωση Σκορ", callback_data="refresh_scores")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("🔄 Ενημέρωση σκορ...")
    if query.data == "refresh_scores":
        await start_command(update, context)

def main():
    if not TELEGRAM_BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN missing!")
        return

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(button_handler))

    print("Dynamic Stats Tracker Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
