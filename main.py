import os
import logging
import requests
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY")

def fetch_todays_matches():
    """
    Τραβάει τους πραγματικούς σημερινούς αγώνες από το API-Football
    και φιλτράρει το ανδρικό ποδόσφαιρο.
    """
    if not RAPIDAPI_KEY:
        logging.error("RAPIDAPI_KEY missing!")
        return []

    today_date = datetime.now().strftime("%Y-%m-%d")
    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
    querystring = {"date": today_date, "season": "2026"}
    
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
    }

    try:
        response = requests.get(url, headers=headers, params=querystring, timeout=10)
        data = response.json()
        
        if "response" not in data:
            return []

        clean_matches = []
        for fixture in data["response"]:
            league_name = fixture.get("league", {}).get("name", "")
            country = fixture.get("league", {}).get("country", "")
            home_team = fixture.get("teams", {}).get("home", {}).get("name", "")
            away_team = fixture.get("teams", {}).get("away", {}).get("name", "")
            status_short = fixture.get("fixture", {}).get("status", {}).get("short", "NS")
            goals_home = fixture.get("goals", {}).get("home", 0)
            goals_away = fixture.get("goals", {}).get("away", 0)
            fixture_date = fixture.get("fixture", {}).get("date", "")

            # Μετατροπή ώρας
            try:
                dt_obj = datetime.fromisoformat(fixture_date.replace("Z", "+00:00"))
                time_str = dt_obj.strftime("%H:%M")
            except:
                time_str = "--:--"

            # Αποκλεισμός γυναικείου ποδοσφαίρου
            text_check = f"{home_team} {away_team} {league_name}".lower()
            if any(term in text_check for term in ["women", "wsl", "liga f", "gynaikeion", "(γ)"]):
                continue

            score_str = f"{goals_home} - {goals_away}" if status_short != "NS" else "VS"
            
            clean_matches.append({
                "time": time_str,
                "league": f"⚽ {country} - {league_name}",
                "match": f"{home_team} {score_str} {away_team}",
                "status": status_short
            })

        return clean_matches[:15] # Επιστρέφει τους πρώτους 15 αγώνες της ημέρας

    except Exception as e:
        logging.error(f"Error: {e}")
        return []

def format_matches_message(matches_list):
    if not matches_list:
        return "ℹ️ Δεν βρέθηκαν διαθέσιμοι αγώνες για σήμερα από το API."

    msg = "📊 **ΣΗΜΕΡΙΝΟΙ ΑΓΩΝΕΣ & LIVE SCORE**\n\n"
    for m in matches_list:
        msg += f"⏰ `{m['time']}` | {m['league']}\n"
        msg += f"🔥 **{m['match']}** (Status: `{m['status']}`)\n"
        msg += "----------------------------------------\n"

    msg += "\n🔄 *Πατήστε Ανανέωση για ζωντανή ενημέρωση.*"
    return msg

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    matches = fetch_todays_matches()
    text = format_matches_message(matches)

    keyboard = [[InlineKeyboardButton("🔄 Ανανέωση Σκορ", callback_data="refresh_scores")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("🔄 Ανάκτηση live σκορ...")
    if query.data == "refresh_scores":
        await start_command(update, context)

def main():
    if not TELEGRAM_BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN missing!")
        return

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(button_handler))

    print("Stats Tracker Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
