import os
import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHANNEL_USERNAME = os.environ.get("CHANNEL_USERNAME", "your_channel_name") # Ορίζεται από το Railway

def get_greece_time():
    """Επιστρέφει την τρέχουσα ώρα Ελλάδας."""
    try:
        return datetime.now(ZoneInfo("Europe/Athens"))
    except:
        return datetime.now()

def format_lifestyle_message():
    current_time_str = get_greece_time().strftime("%H:%M")
    
    msg = "✨ **LIFESTYLE & GOSSIP NEWS HUB** 🌟\n"
    msg += f"🕒 Τελευταία Ενημέρωση: `{current_time_str}` (Ώρα Ελλάδος)\n"
    msg += "----------------------------------------\n\n"
    
    msg += "🔥 **HOT TOPICS & ΤΑΣΕΙΣ ΣΗΜΕΡΑ**\n"
    msg += "• Τελευταία νέα από τον κόσμο της showbiz και της ψυχαγωγίας.\n"
    msg += "• Αποκλειστικά ρεπορτάζ, lifestyle trends και κοσμικά γεγονότα.\n"
    msg += "• Τάσεις της μόδας, τηλεόραση και social media buzz.\n\n"

    msg += "📌 **ΚΑΤΗΓΟΡΙΕΣ ΕΝΗΜΕΡΩΣΗΣ**\n"
    msg += "• 🌟 Showbiz & Celebrities\n"
    msg += "• 🎬 Cinema & TV Shows\n"
    msg += "• ✈️ Travel & Trends\n"
    msg += "----------------------------------------\n"

    msg += "\n💬 *Μείνετε συντονισμένοι για τα επόμενα άρθρα.*"
    return msg

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = format_lifestyle_message()
    
    channel_url = f"https://t.me/{CHANNEL_USERNAME}"
    keyboard = [
        [InlineKeyboardButton("🔄 Ανανέωση Ροής", callback_data="refresh_lifestyle")],
        [InlineKeyboardButton("📢 Μετάβαση στο Κανάλι", url=channel_url)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("🔄 Ενημέρωση ροής lifestyle...")
    if query.data == "refresh_lifestyle":
        await start_command(update, context)

def main():
    if not TELEGRAM_BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN missing!")
        return

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(button_handler))

    print("Lifestyle News Bot is running successfully...")
    application.run_polling()

if __name__ == "__main__":
    main()
