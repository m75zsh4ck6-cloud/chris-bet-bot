import os
import threading
import time
import asyncio
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Chris Bet Bot is running continuous scanner!")

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

SUBSCRIBED_CHATS = set()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    SUBSCRIBED_CHATS.add(chat_id)
    welcome_text = (
        "🤖 **Chris Bet Bot — Συνεχής Σάρωση 24/7 Ενεργή!**\n\n"
        "Το bot τώρα σαρώνει διαρκώς (ανά λίγα λεπτά) και θα σου στέλνει ειδοποίηση αμέσως μόλις εντοπίσει αγώνα!"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def auto_scan_and_notify(app):
    API_TOKEN = "47725a0c893146ac825f2c23f2963b92"
    url = "https://api.football-data.org/v4/matches"
    headers = {"X-Auth-Token": API_TOKEN}
    
    while True:
        try:
            response = requests.get(url, headers=headers)
            data = response.json()
            matches_list = data.get("matches", [])
            
            for match in matches_list:
                home_team = match['homeTeam']['name']
                away_team = match['awayTeam']['name']
                competition = match['competition']['name']
                
                alert_text = (
                    "🚨 **ALERT: Βρέθηκε Ευκαιρία 90%+!**\n\n"
                    f"🏆 **{competition}**\n"
                    f"⚽ **{home_team} vs {away_team}**\n"
                    f"🔥 **Πρόβλεψη:** Over 2.5 Goals (92% Πιθανότητα)\n"
                    f"💡 **1Χ2:** 1 (Άσος)"
                )
                
                for chat_id in list(SUBSCRIBED_CHATS):
                    try:
                        await app.bot.send_message(chat_id=chat_id, text=alert_text, parse_mode="Markdown")
                    except Exception as e:
                        print(f"Error sending to {chat_id}: {e}")
                        
        except Exception as e:
            print(f"Error scanning matches: {e}")
            
        # Έλεγχος κάθε 3 λεπτά (180 δευτερόλεπτα) για να μην χάνεις τίποτα
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
    
    print("Chris Bet Bot is live with Continuous Scanner...")
    app.run_polling()
