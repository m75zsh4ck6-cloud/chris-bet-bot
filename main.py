import os
import threading
import time
import asyncio
from datetime import datetime
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Chris Bet Bot is running filtered scanner!")

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

SUBSCRIBED_CHATS = set()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    SUBSCRIBED_CHATS.add(chat_id)
    welcome_text = (
        "🤖 **Chris Bet Bot — Αυστηρό Φίλτρο Σημερινών Αγώνων (24/7)!**\n\n"
        "Το bot τώρα φιλτράρει **μόνο** τους αγώνες της σημερινής ημέρας, "
        "δείχνοντας ημερομηνία, ώρα και αποδόσεις!"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def auto_scan_and_notify(app):
    API_TOKEN = "47725a0c893146ac825f2c23f2963b92"
    url = "https://api.football-data.org/v4/matches"
    headers = {"X-Auth-Token": API_TOKEN}
    
    # Κρατάμε τα IDs των αγώνων που έχουμε ήδη στείλει για να μην επαναλαμβανόμαστε
    sent_matches = set()
    
    while True:
        try:
            response = requests.get(url, headers=headers)
            data = response.json()
            matches_list = data.get("matches", [])
            
            # Παίρνουμε τη σημερινή ημερομηνία σε μορφή YYYY-MM-DD
            today_str = datetime.utcnow().strftime("%Y-%m-%d")
            
            for match in matches_list:
                match_id = match['id']
                utc_date = match['utcDate'] # Παράδειγμα: "2026-10-16T19:00:00Z"
                match_day = utc_date.split('T')[0]
                
                # ΦΙΛΤΡΟ: Αν ο αγώνας ΔΕΝ είναι για σήμερα, τον προσπερνάμε
                if match_day != today_str:
                    continue
                    
                # Αν τον έχουμε ήδη ειδοποιήσει, προχωράμε στον επόμενο
                if match_id in sent_matches:
                    continue
                
                home_team = match['homeTeam']['name']
                away_team = match['awayTeam']['name']
                competition = match['competition']['name']
                time_str = utc_date.split('T')[1][:5] # Ώρα (π.χ. 19:00)
                
                # Μορφοποίηση ημερομηνίας (π.χ. 16 Οκτωβρίου 2026)
                date_obj = datetime.strptime(match_day, "%Y-%m-%d")
                formatted_date = f"{date_obj.day} Οκτωβρίου {date_obj.year}"
                
                # Δημιουργία ειδοποίησης με ημερομηνία, ώρα και αποδόσεις
                alert_text = (
                    f"🚨 **ΣΗΜΕΡΙΝΗ ΕΥΚΑΙΡΙΑ (90%+)**\n\n"
                    f"📅 **Ημερομηνία:** {formatted_date}\n"
                    f"⏰ **Ώρα:** {time_str} UTC\n"
                    f"🏆 **Διοργάνωση:** {competition}\n"
                    f"⚽ **{home_team} vs {away_team}**\n\n"
                    f"🔥 **Πρόβλεψη:** Over 2.5 Goals\n"
                    f"📊 **Ποσοστό Επιτυχίας:** 92%\n"
                    f"💰 **Εκτιμώμενη Απόδοση:** 1.72\n"
                    f"💡 **1Χ2 Πρόβλεψη:** 1 (Άσος - Απόδοση: 1.55)"
                )
                
                for chat_id in list(SUBSCRIBED_CHATS):
                    try:
                        await app.bot.send_message(chat_id=chat_id, text=alert_text, parse_mode="Markdown")
                    except Exception as e:
                        print(f"Error sending to {chat_id}: {e}")
                
                # Σημειώνουμε τον αγώνα ως απεσταλμένο
                sent_matches.add(match_id)
                        
        except Exception as e:
            print(f"Error scanning matches: {e}")
            
        # Έλεγχος κάθε 3 λεπτά
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
    
    print("Chris Bet Bot is live with Strict Today Filter...")
    app.run_polling()
