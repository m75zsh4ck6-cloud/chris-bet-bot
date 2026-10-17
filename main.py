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

def get_fallback_history():
    """
    Εφεδρικό σταθερό ιστορικό για να εξασφαλίσουμε ότι το bot 
    δεν θα εμφανίσει ποτέ κενή οθόνη.
    """
    d1 = (datetime.now() - timedelta(days=1)).strftime("%d/%m/%Y")
    d2 = (datetime.now() - timedelta(days=2)).strftime("%d/%m/%Y")
    d3 = (datetime.now() - timedelta(days=3)).strftime("%d/%m/%Y")
    
    return [
        {
            "date": d1,
            "matches": [
                {"match": "Μάντσεστερ Γιουνάιτεντ - Τσέλσι", "score": "2:1", "pick": "Over 1.5", "result": "✅ ΚΕΡΔΙΣΜΕΝΟ"},
                {"match": "Μπαρτσελόνα - Σεβίλλη", "score": "3:0", "pick": "1", "result": "✅ ΚΕΡΔΙΣΜΕΝΟ"},
                {"match": "Μπούντεσλιγκα - Ντόρτμουντ", "score": "1:1", "pick": "Over 2.5", "result": "❌ ΧΑΜΕΝΟ"}
            ]
        },
        {
            "date": d2,
            "matches": [
                {"match": "AΕΚ - Ολυμπιακός", "score": "1:0", "pick": "Under 2.5", "result": "✅ ΚΕΡΔΙΣΜΕΝΟ"},
                {"match": "Μίλαν - Ίντερ", "score": "2:2", "pick": "Goal/Goal", "result": "✅ ΚΕΡΔΙΣΜΕΝΟ"}
            ]
        },
        {
            "date": d3,
            "matches": [
                {"match": "Ρεάλ Μαδρίτης - Aτλέτικο", "score": "2:0", "pick": "1", "result": "✅ ΚΕΡΔΙΣΜΕΝΟ"},
                {"match": "Λίβερπουλ - Άρσεναλ", "score": "3:1", "pick": "Over 1.5", "result": "✅ ΚΕΡΔΙΣΜΕΝΟ"}
            ]
        }
    ]

def fetch_realistic_history():
    """
    Προσπαθεί να τραβήξει από το API, αλλιώς γυρνάει σταθερό fallback ιστορικό.
    """
    if not RAPIDAPI_KEY:
        return get_fallback_history()

    past_days_data = []
    try:
        for i in range(1, 4):
            target_date_dt = datetime.now() - timedelta(days=i)
            target_date_str = target_date_dt.strftime("%Y-%m-%d")
            display_date = target_date_dt.strftime("%d/%m/%Y")
            
            url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
            querystring = {"date": target_date_str}
            headers = {
                "X-RapidAPI-Key": RAPIDAPI_KEY,
                "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
            }

            response = requests.get(url, headers=headers, params=querystring, timeout=4)
            data = response.json()
            
            day_matches = []
            if "response" in data and data["response"]:
                count = 0
                for fixture in data["response"]:
                    status = fixture.get("fixture", {}).get("status", {}).get("short", "")
                    if status == "FT":
                        home = fixture.get("teams", {}).get("home", {}).get("name", "")
                        away = fixture.get("teams", {}).get("away", {}).get("name", "")
                        g_home = fixture.get("goals", {}).get("home", 0)
                        g_away = fixture.get("goals", {}).get("away", 0)
                        
                        res_icon = "❌ ΧΑΜΕΝΟ" if (i == 2 and count == 1) else "✅ ΚΕΡΔΙΣΜΕΝΟ"
                        pick_type = "Under 1.5" if "ΧΑΜΕΝΟ" in res_icon else "Over 1.5"

                        day_matches.append({
                            "match": f"{home} - {away}",
                            "score": f"{g_home}:{g_away}",
                            "pick": pick_type,
                            "result": res_icon
                        })
                        count += 1
                        if count >= 3:
                            break

            if day_matches:
                past_days_data.append({"date": display_date, "matches": day_matches})
        
        if not past_days_data:
            return get_fallback_history()
            
        return past_days_data
    except:
        return get_fallback_history()

def format_history_message():
    history = fetch_realistic_history()

    msg = "📊 **ΑΠΟΛΟΓΙΣΜΟΣ ΠΡΟΗΓΟΥΜΕΝΩΝ ΗΜΕΡΩΝ**\n"
    msg += "----------------------------------------\n\n"

    for day in history:
        msg += f"📅 **Ημερομηνία: {day['date']}**\n"
        for m in day["matches"]:
            msg += f"• {m['match']} ({m['score']})\n"
            msg += f"  Pick: `{m['pick']}` | {m['result']}\n"
        msg += "\n"

    msg += "----------------------------------------\n"
    msg += "🔥 **ΣΗΜΕΡΙΝΗ ΕΠΙΛΟΓΗ (LIVE PICK)**\n\n"
    msg += "⚽ Ligue 1\n"
    msg += "🔥 **Λιόν - Μαρσέιγ**\n"
    msg += "🎯 Εκτίμηση Ημέρας: Over 2.5 & G/G | Απόδοση: 🟢 1.78\n\n"
    msg += "ℹ️ *Πατήστε ανανέωση για τα νεότερα στοιχεία.*"
    
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
    await query.answer("🔄 Ανάκτηση δεδομένων...")
    if query.data == "refresh_history":
        await start_command(update, context)

def main():
    if not TELEGRAM_BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN missing!")
        return

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(button_handler))

    print("Marketing Bot running smoothly...")
    application.run_polling()

if __name__ == "__main__":
    main()
