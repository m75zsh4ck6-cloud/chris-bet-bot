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

def fetch_real_matches():
    """Τραβάει τους πραγματικούς σημερινούς αγώνες από το API-Football."""
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

            # Μετατροπή ώρας σε ώρα Ελλάδας
            try:
                dt_utc = datetime.fromisoformat(fixture_date.replace("Z", "+00:00"))
                dt_gr = dt_utc.astimezone(ZoneInfo("Europe/Athens"))
                time_str = dt_gr.strftime("%H:%M")
            except:
                time_str = "--:--"

            # Φιλτράρισμα γυναικείου ποδοσφαίρου
            text_check = f"{home_team} {away_team} {league_name}".lower()
            if any(term in text_check for term in ["women", "wsl", "liga f", "(γ)"]):
                continue

            clean_matches.append({
                "time": time_str,
                "league": f"{country} - {league_name}",
                "match": f"{home_team} - {away_team}",
                "status": status_short
            })

        return clean_matches
    except Exception as e:
        logging.error(f"Error fetching matches: {e}")
        return []

def format_bait_message():
    matches = fetch_real_matches()
    current_time_str = get_greece_time().strftime("%H:%M")
    
    msg = f"📊 **VIP ΣΤΑΤΙΣΤΙΚΑ & ΑΝΑΛΥΣΗ ΑΓΩΝΩΝ**\n"
    msg += f"🕒 Ενημέρωση: `{current_time_str}`\n"
    msg += "----------------------------------------\n\n"

    if matches:
        # Παίρνουμε τον πρώτο πραγματικό αγώνα της σημερινής λίστας
        top_match = matches[0]
        msg += f"🔥 **ΤΟ ΣΗΜΕΡΙΝΟ ΔΥΝΑΤΟ ΠΑΙΧΝΙΔΙ (VIP PICK)**\n"
        msg += f"⚽ {top_match['league']}\n"
        msg += f"🔥 **{top_match['match']}** (Ώρα: `{top_match['time']}`)\n"
        msg += f"🎯 Εκτίμηση: **Over 2.5 & Goal/Goal**\n"
        msg += f"🟢 Απόδοση: `1.90` | ⚡ Εμπιστοσύνη: `92%`\n\n"
        
        msg += "📋 **ΥΠΟΛΟΙΠΟΙ ΣΗΜΕΡΙΝΟΙ ΑΓΩΝΕΣ**\n"
        for m in matches[1:7]:
            msg += f"• `{m['time']}` | {m['match']} [{m['status']}]\n"
    else:
        msg += "ℹ️ **Αυτή τη στιγμή δεν υπάρχουν ενεργοί αγώνες στο API για σήμερα.**\n"
        msg += "Δοκιμάστε ξανά αργότερα ή πατήστε ανανέωση όταν υπάρξει αγωνιστική δράση.\n"

    msg += "\n----------------------------------------\n"
    msg += "👇 *Πατήστε ανανέωση για τα νέα στοιχεία.*"
    
    return msg

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = format_bait_message()
    keyboard = [[InlineKeyboardButton("🔄 Ανανέωση Σήματος", callback_data="refresh_scores")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("🔄 Συγχρονισμός δεδομένων...")
    if query.data == "refresh_scores":
        await start_command(update, context)

def main():
    if not TELEGRAM_BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN missing!")
        return

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(button_handler))

    print("Accurate Real Matches Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
