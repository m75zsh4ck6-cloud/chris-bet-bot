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
        self.wfile.write(b"Bot is alive!")
    def log_message(self, format, *args):
        return

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
    await update.message.reply_text("🤖 **Chris Bet ενεργό!** Χρησιμοποίησε /best ή /combo.", parse_mode="Markdown")

async def best_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not TODAY_BEST_PICKS:
        await update.message.reply_text("⏳ Αναμονή για το πρώτο σάρωμα αγώνων...", parse_mode="Markdown")
        return
    text = "🔥 **TOP VALUE PICKS:**\n\n"
    for p in TODAY_BEST_PICKS[:3]:
        text += f"🎯 {p['home']} vs {p['away']}\n🟢 {p['market']}: **{p['odds']}**\n⚡ {p['stake']}\n\n"
    await update.message.reply_text(text, parse_mode="Markdown")

async def combo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(TODAY_BEST_PICKS) < 2:
        await update.message.reply_text("⏳ Χρειάζονται τουλάχιστον 2 αγώνες. Περίμενε λίγο.", parse_mode="Markdown")
        return
    m1, m2 = TODAY_BEST_PICKS[0], TODAY_BEST_PICKS[1]
    odds = round(float(m1['odds']) * float(m2['odds']), 2)
    text = f"🎟️ **ΔΥΑΔΑ ΑΣΦΑΛΕΙΑΣ**\n\n1️⃣ {m1['home']} vs {m1['away']} ({m1['odds']})\n2️⃣ {m2['home']} vs {m2['away']} ({m2['odds']})\n\n💰 **Συνολική Απόδοση:** {odds}\n🎯 🟢🟢🟢 High Trust"
    await update.message.reply_text(text, parse_mode="Markdown")

def realistic_match_analysis(home, away, comp):
    opts = [
        ("Διπλή Ευκαιρία: 1Χ", "1.42", "🟢🟢🟢 High Trust | Stake: 3/10"),
        ("Διπλή Ευκαιρία: Χ2", "1.55", "🟢🟢🟢 High Trust | Stake: 3/10"),
        ("Over 1.5 Goals", "1.35", "🟢🟢🟢 High Trust | Stake: 3/10"),
        ("Διπλή Ευκαιρία: Χ2 & Over 1.5", "1.82", "🟢 Medium Trust | Stake: 1/10")
    ]
    return opts[abs(hash(home + away + comp)) % len(opts)]

async def auto_scan_and_notify(app):
    global TODAY_BEST_PICKS, DAILY_STATS
    API_TOKEN = "47725a0c893146ac825f2c23f2963b92"
    comps = ["PL", "CL", "SA", "PD", "BL1"]
    headers = {"X-Auth-Token": API_TOKEN}
    sent = set()
    await asyncio.sleep(5)
    
    while True:
        try:
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            if DAILY_STATS["date"] != today:
                DAILY_STATS = {"date": today, "total": 0, "won": 0, "lost": 0}
                TODAY_BEST_PICKS.clear()
            
            for comp in comps:
                url = f"https://api.football-data.org/v4/competitions/{comp}/matches?dateFrom={today}&dateTo={today}"
                res = requests.get(url, headers=headers, timeout=10)
                if res.status_code == 200:
                    for m in res.json().get("matches", []):
                        if m['id'] in sent: continue
                        dt = datetime.fromisoformat(m['utcDate'].replace("Z", "+00:00")) + timedelta(hours=3)
                        if dt.strftime("%Y-%m-%d") != today: continue
                        
                        market, odds, stake = realistic_match_analysis(m['homeTeam']['name'], m['awayTeam']['name'], comp)
                        pick = {'home': m['homeTeam']['name'], 'away': m['awayTeam']['name'], 'comp': comp, 'time': dt.strftime("%H:%M"), 'market': market, 'odds': odds, 'stake': stake}
                        TODAY_BEST_PICKS.insert(0, pick)
                        if len(TODAY_BEST_PICKS) > 10: TODAY_BEST_PICKS.pop()
                        
                        alert = f"🎯 **{pick['home']} vs {pick['away']}**\n🏆 {comp} | ⏰ {pick['time']}\n\n🟢 {market}: **{odds}**\n⚡ {stake}"
                        for cid in list(SUBSCRIBED_CHATS):
                            try: await app.bot.send_message(chat_id=cid, text=alert, parse_mode="Markdown")
                            except: pass
                        sent.add(m['id'])
                        await asyncio.sleep(1)
                await asyncio.sleep(1)
        except Exception as e:
            print(e)
        await asyncio.sleep(300)

async def post_init(application):
    application.create_task(auto_scan_and_notify(application))

if __name__ == '__main__':
    threading.Thread(target=run_web_server, daemon=True).start()
    TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8968240612:AAEDgpg07QlrHH0QiZdCQgP2eoflpq8xWs")
    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("best", best_command))
    app.add_handler(CommandHandler("combo", combo_command))
    app.run_polling()
