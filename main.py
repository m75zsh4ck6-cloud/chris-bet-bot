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
# Εδώ διαβάζει το σωστό κανάλι από το Railway, αλλιώς βάζεις εσύ απευθείας το username σου
CHANNEL_USERNAME = os.environ.get("CHANNEL_USERNAME", "StavrosLifestyleNews") 

def get_greece_time():
    """Επιστρέφει την τρέχουσα ώρα Ελλάδας."""
    try:
        return datetime.now(ZoneInfo("Europe/Athens"))
    except:
        return datetime.now()

def format_lifestyle_news():
    current_time_str = get_greece_time().strftime("%H:%M")
    current_date_str = get_greece_time().strftime("%d/%m/%Y")
    
    msg = f"✨ **LIFESTYLE & GOSSIP DAILY NEWS** 🌟\n"
    msg += f"📅 Ημερομηνία: `{current_date_str}` | 🕒 `{current_time_str}`\n"
    msg += "----------------------------------------\n\n"
    
    msg += "🔥 **ΣΗΜΕΡΙΝΑ ΘΕΜΑΤΑ & ΡΕΠΟΡΤΑΖ**\n\n"
    
    msg += "🎬 **1. Νέα μεγάλη παραγωγή ξεκινάει στην Αθήνα!**\n"
    msg += "• *Τι έγινε:* Γνωστός σκηνοθέτης ετοιμάζει νέα διεθνή σειρά και οι οντισιόν ξεκινούν την ερχόμενη εβδομάδα.\n\n"
    
    msg += "🌟 **2. Η εμφάνιση που συζητήθηκε χθες βράδυ**\n"
    msg += "• *Λεπτομέρειες:* Όλα τα βλέμματα έπεσαν στο κόκκινο χαλί και στις εντυπωσιακές δημιουργίες γνωστών σχεδιαστών.\n\n"
    
    msg += "✈️ **3. Top Travel Trend για το τριήμερο**\n"
    msg += "• *Προορισμοί:* Ποιοι είναι οι κορυφαίοι χειμερινοί προορισμοί που επέλεξαν φέτος οι celebrities.\n"
    
    msg += "----------------------------------------\n"
    msg += "👇 *Πατήστε παρακάτω για συνεχή ροή ειδήσεων στο κανάλι μας.*"
    
    return msg

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = format_lifestyle_news()
    
    channel_url = f"https://t.me/{CHANNEL_USERNAME}"
    keyboard = [
        [InlineKeyboardButton("🔄 Ανανέωση Ειδήσεων", callback_data="refresh_news")],
        [InlineKeyboardButton("📢 Μπες στο Κανάλι Ειδήσεων", url=channel_url)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("🔄 Ενημέρωση ροής...")
    if query.data == "refresh_news":
        await start_command(update, context)

def main():
    if not TELEGRAM_BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN missing!")
        return

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(button_handler))

    print("Lifestyle News Bot with real text is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
