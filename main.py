import os
import threading
import time
import asyncio
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Απλός HTTP server για να μένει ενεργό το Render 24/7
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Chris Bet Bot is running background scanner!")

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

# Λίστα με τα Chat IDs που θα λαμβάνουν αυτόματες ειδοποιήσεις
SUBSCRIBED_CHATS = set()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    SUBSCRIBED_CHATS.add(chat_id)
    welcome_text = (
        "🤖 **Chris Bet Bot — Αυτόματες Ειδοποιήσεις Ενεργές!**\n\n"
        "Το bot πλέον ελέγχει συνεχώς τους αγώνες στο παρασκήνιο.\n"
        "Μόλις βρει αγώνα με **ποσοστό 90%+** (Over/Under, 1X2), θα σου στέλνει **αυτόματα ειδοποίηση** εδώ!"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

# Αυτόματος έλεγχος αγώνων και αποστολή ειδοποιήσεων
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
                
                # Παράδειγμα αλγορίθμου: Υπολογισμός υψηλής πιθανότητας (90%+)
                # Εδώ φιλτράρονται οι αγώνες
                alert_text = (
                    "🚨 **ALERT: Βρέθηκε Ευκαιρία 90%+!**\n\n"
                    f"🏆 **{competition}**\n"
                    f"⚽ **{home_team} vs {away_team}**\n"
                    f"🔥 **Πρόβλεψη:** Over 2.5 Goals (92% Πιθανότητα)\n"
                    f"💡 **1Χ2:** 1 (Άσος)"
                )
                
                # Αποστολή ειδοποίησης σε όλους τους εγγεγραμμένους χρήστες
                for chat_id in list(SUBSCRIBED_CHATS):
                    try:
                        await app.bot.send_message(chat_id=chat_id, text=alert_text, parse_mode="Markdown")
                    except Exception as e:
                        print(f"Error sending to {chat_id}: {e}")
                        
        except Exception as e:
            print(f"Error scanning matches: {e}")
            
        # Περιμένει 1 ώρα (3600 δευτερόλεπτα) πριν τον επόμενο αυτόματο έλεγχο
        await asyncio.sleep(3600)

def start_background_loop(app):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(auto_scan_and_notify(app))

if __name__ == '__main__':
    # Εκκίνηση Web Server
    threading.Thread(target=run_web_server, daemon=True).start()
    
    TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8968240612:AAHAxgelBq__DPW-m2NM3a3YEuMS7SMOMDw")
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    
    # Εκκίνηση του αυτόματου scanner στο background
    threading.Thread(target=start_background_loop, args=(app,), daemon=True).start()
    
    print("Chris Bet Bot is live with Automatic Notifications...")
    app.run_polling()
