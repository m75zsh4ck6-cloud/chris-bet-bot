import os
import logging
import requests
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
RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY")

def get_greece_time():
    """Επιστρέφει την τρέχουσα ώρα Ελλάδας."""
    try:
        return datetime.now(ZoneInfo("Europe/Athens"))
    except:
        return datetime.now()

def fetch_stats_matches():
    """Τραβάει τους πραγματικούς σημερινούς αγώνες για στατιστική ανάλυση."""
    if not RAPIDAPI_KEY:
        return []

    today_date = get_greece_time().strftime("%Y-%m-%d")
    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
    querystring = {"date": today_date}
    
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
    }

    try:
        response = requests.get(url, headers=headers, params=querystring, timeout=10)
        data = response.json()
        
        if "response" not in data or not data["response"]:
            return []

        clean_matches = []
        for fixture in data["response"]:
            league_name = fixture.get("league", {}).get("name", "")
            country = fixture.get("league", {}).get("country", "")
            home_team = fixture.get("teams", {}).get("home", {}).get("name", "")
            away_team = fixture.get("teams", {}).get("away", {}).get("name", "")
            status_short = fixture.get("fixture", {}).get("status", {}).get("short", "NS")
            fixture_date = fixture.get("fixture", {}).get("date", "")

            try:
                dt_utc = datetime.fromisoformat(fixture_date.replace("Z", "+00:00"))
                dt_gr = dt_utc.astimezone(ZoneInfo("Europe/Athens"))
                time_str = dt_gr.strftime("%H:%M")
            except:
                time_str = "--:--"

            text_check = f"{home_team} {away_team} {league_name}".lower()
            if any(term in text_check for term in ["women", "wsl", "liga f", "(γ)"]):
                continue

            clean_matches.append({
                "time": time_str,
                "league": f"{country} - {league_name}",
                "match": f"{home_team} vs {away_team}",
                "status": status_short
            })

        return clean_matches
    except Exception as e:
        logging.error(f"Error fetching stats matches: {e}")
        return []

def format_hub_message():
    matches = fetch_stats_matches()
    current_time_str = get_greece_time().strftime("%H:%M")
    
    msg = "📊 **DAILY STATS & NEWS HUB** ⚽\n"
    msg += f"🕒 Τελευταία Ενημέρωση: `{current_time_str}` (Ώρα Ελλάδος)\n"
    msg += "----------------------------------------\n\n"
    
    msg += "📌 **ΚΑΘΗΜΕΡΙΝΗ ΑΝΑΛΥΣΗ & ΣΤΑΤΙΣΤΙΚΑ**\n"
    msg += "• Εδώ θα βρίσκετε καθημερινά ενημερωτικά δελτία φόρμες ομάδων και ειδήσεις.\n"
    msg += "• *Στόχος μας η καθαρή ενημέρωση δεδομένων.*\n\n"

    msg += "🔥 **ΣΗΜΕΡΙΝΟ ΠΡΟΓΡΑΜΜΑ & LIVE SCORES**\n"
    
    if matches:
        for m in matches[:8]:  # Εμφανίζει έως 8 αγώνες
            msg += f"⏰ `{m['time']}` | {m['league']}\n"
            msg += f"⚽ **{m['match']}** [Status: `{m['status']}`]\n"
            msg += "----------------------------------------\n"
    else:
        msg += "ℹ️ Δεν βρέθηκαν ενεργοί αγώνες στο API για αυτή τη χρονική στιγμή.\n"
        msg += "----------------------------------------\n"

    msg += "\n⚠️ *21+ | Παίξτε Υπεύθυνα. Υπηρεσία στατιστικής ανάλυσης.*"
    return msg

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = format_hub_message()
    
    # Δημιουργία καθαρών, νόμιμων επιλογών (π.χ. ανανέωση και ενημερωτικό site/link)
    keyboard = [
        [InlineKeyboardButton("🔄 Ανανέωση Δεδομένων", callback_data="refresh_hub")],
        [InlineKeyboardButton("📢 Επίσημο Κανάλι Ειδήσεων", url="https://t.me/your_channel_link")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("🔄 Ενημέρωση στατιστικών...")
    if query.data == "refresh_hub":
        await start_command(update, context)

def main():
    if not TELEGRAM_BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN missing!")
        return

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(button_handler))

    print("Legal Stats Hub Bot is running successfully...")
    application.run_polling()

if __name__ == "__main__":
    main()
