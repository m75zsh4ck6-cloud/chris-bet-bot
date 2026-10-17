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

def get_strong_track_record():
    """
    Δημιουργεί δυναμικά τις προηγούμενες 3 ημέρες με ακριβείς ημερομηνίες 
    και κορυφαία ζευγάρια αγώνων για μέγιστη αξιοπιστία.
    """
    d1 = (datetime.now() - timedelta(days=1)).strftime("%d/%m/%Y")
    d2 = (datetime.now() - timedelta(days=2)).strftime("%d/%m/%Y")
    d3 = (datetime.now() - timedelta(days=3)).strftime("%d/%m/%Y")
    
    return [
        {
            "date": d1,
            "matches": [
                {"match": "Real Madrid - Barcelona", "score": "2:1", "pick": "Goal / Goal", "odds": "1.72", "result": "✅ ΚΕΡΔΙΣΜΕΝΟ"},
                {"match": "Bayern Munich - Dortmund", "score": "3:1", "pick": "Over 2.5", "odds": "1.65", "result": "✅ ΚΕΡΔΙΣΜΕΝΟ"},
                {"match": "PSG - Marseille", "score": "1:1", "pick": "1 (Άσος)", "odds": "1.80", "result": "❌ ΧΑΜΕΝΟ"}
            ]
        },
        {
            "date": d2,
            "matches": [
                {"match": "Arsenal - Liverpool", "score": "2:2", "pick": "Over 1.5", "odds": "1.40", "result": "✅ ΚΕΡΔΙΣΜΕΝΟ"},
                {"match": "Inter - Juventus", "score": "1:0", "pick": "Under 2.5", "odds": "1.75", "result": "✅ ΚΕΡΔΙΣΜΕΝΟ"}
            ]
        },
        {
            "date": d3,
            "matches": [
                {"match": "AC Milan - Napoli", "score": "2:0", "pick": "1Χ & Under 3.5", "odds": "1.52", "result": "✅ ΚΕΡΔΙΣΜΕΝΟ"},
                {"match": "Manchester City - Chelsea", "score": "3:2", "pick": "Over 2.5", "odds": "1.68", "result": "✅ ΚΕΡΔΙΣΜΕΝΟ"}
            ]
        }
    ]

def format_history_message():
    history = get_strong_track_record()
    today_str = datetime.now().strftime("%d/%m/%Y")

    msg = f"📊 **ΕΠΙΣΗΜΟΣ ΑΠΟΛΟΓΙΣΜΟΣ (WHATSAPP/TELEGRAM ARCHIVE)**\n"
    msg += f"🗓️ Ενημέρωση: `{today_str}`\n"
    msg += "----------------------------------------\n\n"

    for day in history:
        msg += f"📅 **Ημερομηνία: {day['date']}**\n"
        for m in day["matches"]:
            msg += f"• **{m['match']}** (`{m['score']}`)\n"
            msg += f"  🎯 Pick: `{m['pick']}` | 🟢 Απόδοση: `{m['odds']}` | {m['result']}\n"
        msg += "\n"

    msg += "----------------------------------------\n"
    msg += "🔥 **ΤΟ ΔΥΝΑΤΟ ΤΥΡΑΚΙ ΣΗΜΕΡΑ (VIP PICK)**\n\n"
    msg += "⚽ Αγγλία - Premier League\n"
    msg += "🔥 **Manchester United - Tottenham**\n"
    msg += "🎯 Εκτίμηση: **Over 2.5 & Goal/Goal**\n"
    msg += "🟢 Απόδοση: `1.95` | ⚡ Εμπιστοσύνη: `95%`\n\n"
    msg += "👇 *Πατήστε ανανέωση για τα επόμενα σήματα.*"
    
    return msg

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = format_history_message()
    keyboard = [[InlineKeyboardButton("🔄 Ανανέωση Σήματος", callback_data="refresh_history")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("🔄 Συγχρονισμός δεδομένων...")
    if query.data == "refresh_history":
        await start_command(update, context)

def main():
    if not TELEGRAM_BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN missing!")
        return

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(button_handler))

    print("Strong Marketing Bot running successfully...")
    application.run_polling()

if __name__ == "__main__":
    main()
