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
DAILY_STATS = {"date": "", "total": 0, "won": 0, "lost": 0}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    SUBSCRIBED_CHATS.add(chat_id)
    welcome_text = (
        "🤖 **Chris Bet — Clean Pro Edition (24/7)!**\n\n"
        "Το bot ενεργοποιήθηκε σε καθαρή μορφή!\n"
        "• Χρησιμοποίησε **/best** για τα κορυφαία σημεία.\n"
        "• Χρησιμοποίησε **/combo** για έτοιμη Δυάδα Ασφαλείας!\n"
        "• Ο ημερήσιος απολογισμός αποτελεσμάτων στέλνεται αυτόματα."
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
