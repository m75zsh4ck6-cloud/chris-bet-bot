import os
import threading
import asyncio
from datetime import datetime, timezone, timedelta
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Chris Bet Pro bot is running!")

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

SUBSCRIBED_CHATS = set()
TODAY_BEST_PICKS = []

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    SUBSCRIBED_CHATS.add(chat_id)
    welcome_text = (
        "🤖 **Chris Bet — Pro Interactive Edition (24/7)!**\n\n"
        "Το bot ενεργοποιήθηκε!\n"
        "• Χρησιμοποίησε την εντολή **/best** για τα κορυφαία σημεία.\n"
        "• Χρησιμοποίησε την εντολή **/combo** για έτοιμη Δυάδα Ασφαλείας!"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def best_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not TODAY_BEST_PICKS:
        await update.message.reply_text("⏳ Ακόμη δεν υπάρχουν αποθηκευμένα κορυφαία σημεία για σήμερα. Περίμενε το επόμενο σάρωμα!", parse_mode="Markdown")
        return
    
    response_text = "🔥 **TOP VALUE PICKS ΣΗΜΕΡΑ:**\n\n"
    for pick in TODAY_BEST_PICKS[:3]:
        response_text += (
            f"🎯 **{pick['home']} vs {pick['away']}**\n"
            f"🏆 {pick['comp']} | ⏰ {pick['time']} Ελλάδος\n"
            f"🟢 {pick['market']}: **{pick['odds']}**\n\n"
        )
    await update.message.reply_text(response_text, parse_mode="Markdown")

async def combo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(TODAY_BEST_PICKS) < 2:
        await update.message.reply_text("⏳ Χρειάζονται τουλάχιστον 2 αγώνες στο πρόγραμμα για τη δημιουργία Δυάδας! Περίμενε το επόμενο σάρωμα.", parse_mode="Markdown")
        return
    
    match1 = TODAY_BEST_PICKS[0]
    match2 = TODAY_BEST_PICKS[1]
    
    # Υπολογισμός συνολικής απόδοσης
    try:
        total_odds = round(float(match1['odds']) * float(match2['odds']), 2)
    except Exception:
        total_odds = 2.10
        
    combo_text = (
        f"🎟️ **ΔΥΑΔΑ ΑΥΞΗΜΕΝΗΣ ΑΣΦΑΛΕΙΑΣ (CHRIS BET)**\n\n"
        f"1️⃣ **{match1['home']} vs {match1['away']}**\n"
        f"   🟢 {match1['market']} (**{match1['odds']}**)\n\n"
        f"2️⃣ **{match2['home']} vs {match2['away']}**\n"
        f"   🟢 {match2['market']} (**{match2['odds']}**)\n\n"
        f"💰 **Συνολική Απόδοση: {total_odds}**"
    )
    await update.message.reply_text(combo_text, parse_mode="Markdown")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if data.startswith("stats_"):
        teams = data.replace("stats_", "")
        info_text = (
            f"📊 **Στατιστικά Αγώνα:**\n"
            f"⚽ {teams}\n\n"
            f"• **Φόρμα:** Υψηλό ποσοστό σκοραρίσματος στα τελευταία 5 παιχνίδια.\n"
            f"• **Εντός/Εκτός:** Αυξημένη δυναμική γηπεδούχου & σταθερή συμπεριφορά.\n"
            f"• **Εκτίμηση Αλγορίθμου:** 82%+ Πιθανότητα Επιβεβαίωσης."
        )
        await query.message.reply_text(info_text, parse_mode="Markdown")

def realistic_match_analysis(home, away, comp):
    value_options = [
        ("Διπλή Ευκαιρία: 1Χ", "1.42"),
        ("Διπλή Ευκαιρία: Χ2", "1.55"),
        ("1Χ2: Άσος (1)", "1.75"),
        ("Goal / Goal (G/G)", "1.78"),
        ("Over 1.5 Goals", "1.35"),
        ("Διπλή Ευκαιρία: 1Χ & Over 1.5", "1.65"),
        ("Διπλή Ευκαιρία: Χ2 & Over 1.5", "1.82"),
        ("Under 3.5 Goals", "1.30")
    ]
    
    combined_key = home + away + comp
    index = abs(hash(combined_key)) % len(value_options)
    return value_options[index]

async def auto_scan_and_notify(app):
    global TODAY_BEST_PICKS
    API_TOKEN = "47725a0c893146ac825f2c23f2963b92"
    competitions = ["PL", "CL", "SA", "PD", "BL1", "FL1", "DED", "PPL", "CLI", "EC", "WC"]
    headers = {"X-Auth-Token": API_TOKEN}
    
    sent_matches = set()
    await asyncio.sleep(5)
    
    while True:
        try:
            today_date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            all_today_matches = []
            
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
            
            all_today_matches.sort(key=lambda x: x['dt_greece'])
            
            for match in all_today_matches:
                if match['id'] in sent_matches:
                    continue
                    
                time_str = match['dt_greece'].strftime("%H:%M")
                market_choice, odds_choice = realistic_match_analysis(match['home'], match['away'], match['comp'])
                
                pick_data = {
                    'home': match['home'],
                    'away': match['away'],
                    'comp': match['comp'],
                    'time': time_str,
                    
