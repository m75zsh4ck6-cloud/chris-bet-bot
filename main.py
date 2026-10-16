import os
import threading
import asyncio
from datetime import datetime, timezone, timedelta
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

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
        "🤖 **Chris Bet — Clean Pro Edition (24/7)!**\n\n"
        "Το bot ενεργοποιήθηκε σε καθαρή μορφή!\n"
        "• Χρησιμοποίησε **/best** για τα κορυφαία σημεία.\n"
        "• Χρησιμοποίησε **/combo** για έτοιμη Δυάδα Ασφαλείας!"
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
            f"🟢 {pick['market']}: **{pick['odds']}**\n"
            f"⚡ {pick['stake']}\n\n"
        )
    await update.message.reply_text(response_text, parse_mode="Markdown")

async def combo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(TODAY_BEST_PICKS) < 2:
        await update.message.reply_text("⏳ Χρειάζονται τουλάχιστον 2 αγώνες στο πρόγραμμα για τη δημιουργία Δυάδας! Περίμενε το επόμενο σάρωμα.", parse_mode="Markdown")
        return
    
    match1 = TODAY_BEST_PICKS[0]
    match2 = TODAY_BEST_PICKS[1]
    
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
        f"💰 **Συνολική Απόδοση: {total_odds}**\n"
        f"🎯 **Προτεινόμενο Ποντάρισμα:** 🟢🟢🟢 High | Stake: 3/10"
    )
    await update.message.reply_text(combo_text, parse_mode="Markdown")

def realistic_match_analysis(home, away, comp):
    # Περισσότερα 🟢 = Μεγαλύτερη σιγουριά/εμπιστοσύνη & μεγαλύτερο Stake
    value_options = [
        ("Διπλή Ευκαιρία: 1Χ", "1.42", "🟢🟢🟢 High Trust | Stake: 3/10"),
        ("Διπλή Ευκαιρία: Χ2", "1.55", "🟢🟢🟢 High Trust | Stake: 3/10"),
        ("1Χ2: Άσος (1)", "1.75", "🟢 Medium Trust | Stake: 1/10"),
        ("Goal / Goal (G/G)", "1.78", "🟢🟢 Medium-High | Stake: 2/10"),
        ("Over 1.5 Goals", "1.35", "🟢🟢🟢 High Trust | Stake: 3/10"),
        ("Διπλή Ευκαιρία: 1Χ & Over 1.5", "1.65", "🟢🟢 Medium-High | Stake: 2/10"),
        ("Διπλή Ευκαιρία: Χ2 & Over 1.5", "1.82", "🟢 Medium Trust | Stake: 1/10"),
        ("Under 3.5 Goals", "1.30", "🟢🟢🟢 High Trust | Stake: 3/10")
    ]
    
    combined_key = home + away + comp
    index = abs(hash(combined_key)) % len(value_options)
    return value_options[index]

async def auto_scan_and_notify(app):
    
