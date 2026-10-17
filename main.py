import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# --- Ο ΑΛΓΟΡΙΘΜΟΣ ΜΕ ΤΑ ΦΙΛΤΡΑ ΚΑΙ ΤΑ ΣΗΜΕΙΑ ΣΟΥ (Σ στα ελληνικά) ---
def get_matches():
    return [
        {
            "match": "FC Bayern München vs RB Leipzig",
            "pick": "Διπλή Ευκαιρία: X2 & Over 1.5",
            "odds": "1.82",
            "trust": "Μεσαία Εμπιστοσύνη",
            "stars": "⚡",
            "stake": "1/10",
            "confidence": 85
        },
        {
            "match": "FC Schalke 04 vs 1. FSV Mainz 05",
            "pick": "Διπλή Ευκαιρία: 1X",
            "odds": "1.42",
            "trust": "Υψηλή Εμπιστοσύνη",
            "stars": "⚡Εξαιρετική",
            "stake": "3/10",
            "confidence": 95  # >= 95% Σιγουριά
        },
        {
            "match": "SV 07 Elversberg vs FC Augsburg",
            "pick": "Over 1.5 Goals",
            "odds": "1.35",
            "trust": "Υψηλή Εμπιστοσύνη",
            "stars": "⚡Εξαιρετική",
            "stake": "3/10",
            "confidence": 98  # >= 95% Σιγουριά
        }
    ]

def format_picks_message(matches_list, header="🔥 ΚΟΡΥΦΑΙΕΣ ΕΠΙΛΟΓΕΣ:"):
    if not matches_list:
        return "Δεν βρέθηκαν διαθέσιμοι αγώνες αυτή τη στιγμή."
    
    msg = f"{header}\n\n"
    for m in matches_list:
        msg += f"🎯 {m['match']}\n"
        msg += f"👉 {m['pick']} | Απόδοση: {m['odds']}\n"
        msg += f"{m['stars']} {m['trust']} | Ποντάρισμα: {m['stake']}\n\n"
    return msg.strip()

# --- HANDLERS ---

# 1. Με το /start φέρνει ΑΜΕΣΩΣ τους αγώνες στα ελληνικά
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    context.bot_data["user_chat_id"] = chat_id  # Αποθήκευση για αυτόματες ειδοποιήσεις
    
    matches = get_matches()
    response_text = format_picks_message(matches, header="🔥 ΚΟΡΥΦΑΙΕΣ ΕΠΙΛΟΓΕΣ:")
    await update.message.reply_text(response_text)

# 2. Αυτόματος έλεγχος για αγώνες με >= 95% σιγουριά
async def check_high_confidence_matches(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.bot_data.get("user_chat_id")
    if not chat_id:
        return  
    
    matches = get_matches()
    top_sure_matches = [m for m in matches if m.get("confidence", 0) >= 95]
    
    if top_sure_matches:
        alert_text = format_picks_message(
            top_sure_matches, 
            header="🚨 ΑΥΤΟΜΑΤΗ ΕΙΔΟΠΟΙΗΣΗ (Σιγουριά ≥ 95%):"
        )
        await context.bot.send_message(chat_id=chat_id, text=alert_text)

def main():
    if not TELEGRAM_BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN is missing!")
        return

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Εντολή /start
    application.add_handler(CommandHandler("start", start_command))

    # Αυτόματος έλεγχος κάθε 1 ώρα (3600 δευτερόλεπτα) για αγώνες >= 95%
    job_queue = application.job_queue
    if job_queue:
        job_queue.run_repeating(check_high_confidence_matches, interval=3600, first=10)

    print("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
