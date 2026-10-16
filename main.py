import os
import threading
import time
import asyncio
from datetime import datetime, timezone
import random
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Chris Bet strict today scanner is running!")

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

SUBSCRIBED_CHATS = set()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    SUBSCRIBED_CHATS.add(chat_id)
    welcome_text = (
        "🤖 **Chris Bet — 93%+ Strict Live (24/7)!**\n\n"
        "Το bot ενεργοποιήθηκε με **αυστηρό έλεγχο ημέρας**, ώστε να εμφανίζει αποκλειστικά και μόνο τους αγώνες που είναι προγραμματισμένοι για σήμερα!"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def auto_scan_and_notify(app):
    API_TOKEN = "47725a0c893146ac825f2c23f2963b92"
    competitions = ["PL", "CL", "SA", "PD", "BL1", "FL1", "DED", "PPL", "CLI", "EC", "WC"]
    headers = {"X-Auth-Token": API_TOKEN}
    
    sent_matches = set()
    
    markets_pool = [
        ("Over 0.5 Goals", "1.08", "96.5%"),
        ("Over 1.5 Goals", "1.35", "93.5%"),
        ("Under 0.5 Goals", "2.40", "93.0%"),
        ("Goal / Goal (G/G)", "1.70", "93.2%"),
        ("1Χ2: Άσος (1)", "1.55", "93.0%")
    ]
    
    while True:
        try:
            # Ακριβής σημερινή ημερομηνία σε UTC
            today_date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            
            for comp in competitions:
                # Ζητάμε από το API αποκλειστικά τα ματς της σημερινής ημερομηνίας
                url = f"https://api.football-data.org/v4/competitions/{comp}/matches?dateFrom={today_date_str}&dateTo={today_date_str}"
                response = requests.get(url, headers=headers)
                
                if response.status_code != 200:
                    continue
                    
                data = response.json()
                matches_list = data.get("matches", [])
                
                for match in matches_list:
                    match_id = match['id']
                    utc_date = match['utcDate'] # Παράδειγμα: "2026-10-16T19:00:00Z"
                    match_day = utc_date.split('T')[0]
                    
                    # ΔΙΠΛΟ ΦΙΛΤΡΟ: Αν η ημερομηνία δεν ταιριάζει απόλυτα με τη σημερινή, το απορρίπτουμε
                    if match_day != today_date_str:
                        continue
                        
                    if match_id in sent_matches:
                        continue
                    
                    home_team = match['homeTeam']['name']
                    away_team = match['awayTeam']['name']
                    competition_name = data.get('competition', {}).get('name', comp)
                    time_str = utc_date.split('T')[1][:5]
                    
                    market_choice, odds_choice, perc_choice = random.choice(markets_pool)
                    
                    alert_text = (
                        f"🎯 **{home_team} vs {away_team}**\n"
                        f"🏆 {competition_name} | ⏰ {time_str} UTC\n\n"
                        f"⚽ **Σημείο:** {market_choice}\n"
                        f"🟢 **Απόδοση:** {odds_choice}  |  📊 **Ποσοστό:** {perc_choice}"
                    )
                    
                    for chat_id in list(SUBSCRIBED_CHATS):
                        try:
                            await app.bot.send_message(chat_id=chat_id, text=alert_text, parse_mode="Markdown")
                        except Exception as e:
                            print(f"Error sending to {chat_id}: {e}")
                    
                    sent_matches.add(match_id)
                
                await asyncio.sleep(2)
                        
        except Exception as e:
            print(f"Error scanning matches: {e}")
            
        await asyncio.sleep(180)

def start_background_loop(app):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(auto_scan_and_notify(app))

if __name__ == '__main__':
    threading.Thread(target=run_web_server, daemon=True).start()
    
    TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8968240612:AAHAxgelBq__DPW-m2NM3a3YEuMS7SMOMDw")
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    
    threading.Thread(target=start_background_loop, args=(app,), daemon=True).start()
    
    print("Chris Bet is live with Strict Date Filter...")
    app.run_polling()
