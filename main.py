import os
import threading
import asyncio
from datetime import datetime, timezone, timedelta
import random
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Chris Bet bot is running!")

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

SUBSCRIBED_CHATS = set()

async def send_matches_to_all(app, matches_list):
    markets_pool = [
        ("Over 0.5 Goals", "1.08"),
        ("Over 1.5 Goals", "1.35"),
        ("Under 0.5 Goals", "2.40"),
        ("Goal / Goal (G/G)", "1.70"),
        ("1Χ2: Άσος (1)", "1.55")
    ]
    
    # Ταξινόμηση χρονολογικά (από τα πιο νωρίς στα πιο αργά)
    matches_list.sort(key=lambda x: x['dt_greece'])
    
    for match in matches_list:
        time_str = match['dt_greece'].strftime("%H:%M")
        market_choice, odds_choice = random.choice(markets_pool)
        
        alert_text = (
            f"🎯 **{match['home']} vs {match['away']}**\n"
            f"🏆 {match['comp']} | ⏰ {time_str} Ελλάδος\n\n"
            f"⚽ **Σημείο:** {market_choice}\n"
            f"🟢 **Απόδοση:** {odds_choice}"
        )
        
        for chat_id in list(SUBSCRIBED_CHATS):
            try:
                await app.bot.send_message(chat_id=chat_id, text=alert_text, parse_mode="Markdown")
            except Exception as e:
                print(f"Error sending to {chat_id}: {e}")
        
        await asyncio.sleep(2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    SUBSCRIBED_CHATS.add(chat_id)
    
    welcome_text = (
        "🤖 **Chris Bet — Sorted by Time (24/7)!**\n\n"
        "Το bot ενεργοποιήθηκε με κανονικές, ρεαλιστικές ώρες αγώνων!"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")
    
    # Σημερινή ημερομηνία με κανονικές, ρεαλιστικές ώρες αγώνων
    today_base = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(hours=3)
    
    sample_matches = [
        {
            'dt_greece': today_base.replace(hour=19, minute=30), # 19:30
            'home': 'Panathinaikos FC',
            'away': 'Olympiacos FC',
            'comp': 'Super League Greece'
        },
        {
            'dt_greece': today_base.replace(hour=21, minute=00), # 21:00
            'home': 'Real Madrid',
            'away': 'FC Barcelona',
            'comp': 'Primera Division'
        },
        {
            'dt_greece': today_base.replace(hour=22, minute=45), # 22:45
            'home': 'AC Milan',
            'away': 'Inter Milan',
            'comp': 'Serie A'
        }
    ]
    
    asyncio.create_task(send_matches_to_all(context.application, sample_matches))

def start_background_loop(app):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    async def background_scanner():
        while True:
            await asyncio.sleep(600)
            
    loop.run_until_complete(background_scanner())

if __name__ == '__main__':
    threading.Thread(target=run_web_server, daemon=True).start()
    
    TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8968240612:AAHAxgelBq__DPW-m2NM3a3YEuMS7SMOMDw")
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    
    print("Chris Bet is live and ready...")
    app.run_polling()
