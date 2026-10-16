import os
import threading
import time
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
        self.wfile.write(b"Chris Bet test scanner is running!")

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

SUBSCRIBED_CHATS = set()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    SUBSCRIBED_CHATS.add(chat_id)
    welcome_text = (
        "🤖 **Chris Bet — Sorted by Time (24/7)!**\n\n"
        "Το bot είναι έτοιμο και σαρώνει συνεχώς τους σημερινούς αγώνες με χρονολογική σειρά!"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def auto_scan_and_notify(app):
    API_TOKEN = "47725a0c893146ac825f2c23f2963b92"
    competitions = ["PL", "CL", "SA", "PD", "BL1", "FL1", "DED", "PPL", "CLI", "EC", "WC"]
    headers = {"X-Auth-Token": API_TOKEN}
    
    sent_matches = set()
    
    markets_pool = [
        ("Over 0.5 Goals", "1.08"),
        ("Over 1.5 Goals", "1.35"),
        ("Under 0.5 Goals", "2.40"),
        ("Goal / Goal (G/G)", "1.70"),
        ("1Χ2: Άσος (1)", "1.55")
    ]
    
    while True:
        try:
            today_date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            all_today_matches = []
            
            # 1. Προσπάθεια ανάγνωσης από το API
            for comp in competitions:
                url = f"https://api.football-data.org/v4/competitions/{comp}/matches?dateFrom={today_date_str}&dateTo={today_date_str}"
                response = requests.get(url, headers=headers)
                
                if response.status_code != 200:
                    continue
                    
                data = response.json()
                matches_list = data.get("matches", [])
                
                for match in matches_list:
                    match_id = match['id']
                    if match_id in sent_matches:
                        continue
                        
                    utc_date_str = match['utcDate']
                    dt_utc = datetime.fromisoformat(utc_date_str.replace("Z", "+00:00"))
                    dt_greece = dt_utc + timedelta(hours=3)
                    
                    match_day = dt_greece.strftime("%Y-%m-%d")
                    if match_day != today_date_str:
                        continue
                        
                    all_today_matches.append({
                        'id': match_id,
                        'dt_greece': dt_greece,
                        'home': match['homeTeam']['name'],
                        'away': match['awayTeam']['name'],
                        'comp': data.get('competition', {}).get('name', comp)
                    })
                
                await asyncio.sleep(1)
            
            # Αν για κάποιο λόγο το API δεν βρει παιχνίδια αυτή τη στιγμή, 
            # βάζουμε προσωρινά παραδείγματα για να δεις αμέσως πώς δουλεύει η σειρά και η εμφάνιση!
            if not all_today_matches:
                now_greece = datetime.now(timezone.utc) + timedelta(hours=3)
                all_today_matches =
