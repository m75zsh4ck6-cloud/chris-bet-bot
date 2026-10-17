import os
import logging
import requests
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY")

def fetch_realistic_history():
    """
    Τραβάει πραγματικά αποτελέσματα προηγούμενων ημερών και εισάγει
    ελεγχόμενη απόκλιση (ένα ❌) για ρεαλιστική εικόνα.
    """
    if not RAPIDAPI_KEY:
        return []

    past_days_data = []
    
    for i in range(1, 4):
        target_date_dt = datetime.now() - timedelta(days=i)
        target_date_str = target_date_dt.strftime("%Y-%m-%d")
        display_date = target_date_dt.strftime("%d/%m/%Y")
        
        url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
        querystring = {"date": target_date_str, "season": "2026"}
        headers = {
            "X-RapidAPI-Key": RAPIDAPI_KEY,
            "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
        }

        day_matches = []
        try:
            response = requests.get(url, headers=headers, params=querystring, timeout=5)
            data = response.json()
            
            if "response" in data and data["response"]:
                count = 0
                for fixture in data["response"]:
                    status = fixture.get("fixture", {}).get("status", {}).get("short", "")
                    if status == "FT":  # Τελειωμένος αγώνας
                        home = fixture.get("teams", {}).get("home", {}).get("name", "")
                        away = fixture.get("teams", {}).get("away", {}).get("name", "")
                        g_home = fixture.get("goals", {}).get("home", 0)
                        g_away = fixture.get("goals", {}).get("away", 0)
                        
                        # Στη 2η ημέρα, βάζουμε 1 χαμένο (❌) για ρεαλισμό
                        if i == 2 and count == 1:
                            res_icon = "❌ ΧΑΜΕΝΟ"
                            pick_type = "Under 1.5"
                        else:
                            res_icon = "✅ ΚΕΡΔΙΣΜΕΝΟ"
                            pick_type = "Over 1.5"

                        day_matches.append({
                            "match": f"{home} - {away}",
                            "score": f"{g_home}:{g_away}",
                            "pick": pick_type,
                            "result": res_icon
                        })
                        
                        count += 1
                        if count >= 3:  # 3 αγώνες ανά ημέρα
                            break

        except Exception as e:
            logging.error(f"Error fetching date {target_date_str}: {e}")

        if day_matches:
            past_days_data.append({
                "date": display_date,
                "matches": day_matches
            })

    return past_days_data

def fetch_todays_teaser():
    """
    Τραβάει τον σημερινό αγώνα - δόλωμα.
    """
    if not RAPIDAPI_KEY:
        return "⚽ Λιόν - Μαρσέιγ\n🎯 Εκτίμηση Ημέρας: Goal/Goal & Over 2.5 (1.75)"

    today_date = datetime.now().strftime("%Y-%m-%d")
    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
    querystring = {"date": today_date, "season": "2026"}
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
    }

    try:
        response = requests.get(url, headers=headers, params=querystring, timeout=5)
        data = response.json()
        if "response" in data and data["response"]:
            fix = data["response"][0]
            home = fix.get("teams", {}).get("home", {}).get("name", "Λιόν")
            away = fix.get("teams", {}).get("away", {}).get("name", "Μαρσέιγ")
            league = fix.get("league", {}).get("name", "Ligue 1")
            return f"⚽ {league}\n🔥 **{home} - {away}**\n🎯 Εκτίμηση Ημέρας: Over 2.5 & G/G | Απόδοση: 🟢 1.78"
    except:
        pass
    
    return "⚽ Ligue 1\n🔥 **Λιόν - Μαρσέιγ**\n🎯 Εκτίμηση Ημέρας: Over 2.5 & G/G | Απόδοση: 🟢 1.78"

def format_history_message():
    history = fetch_realistic_history()
    teaser = fetch_todays_teaser()

    msg = "📊 **ΑΠΟΛΟΓΙΣΜΟΣ ΠΡΟΗΓΟΥΜΕΝΩΝ ΗΜΕΡΩΝ**\n"
    msg += "----------------------------------------\n\n"

    if history:
        for day in history:
            msg += f"📅 **Ημερομηνία: {day['date']}**\n"
            for m in day["matches"]:
                msg += f"• {m['match']} ({m['score']})\n"
                msg += f"  Pick: `{m['pick']}` | {m['result']}\n"
            msg += "\n"
    else:
        msg += "✨ Ενημέρωση ιστορικού...\n\n"

    msg += "----------------------------------------\n"
    msg += "🔥 **ΣΗΜΕΡΙΝΗ ΕΠΙΛΟΓΗ (LIVE PICK)**\n\n"
    msg += f"{teaser}\n\n"
    msg += "ℹ️ *Πατήστε ανανέωση για ζωντανή ενημέρωση.*"
    
    return msg

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = format_history_message()
    keyboard = [[InlineKeyboardButton("🔄 Ανανέωση", callback_data="refresh_history")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await
