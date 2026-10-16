import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Απλός HTTP server για να μένει online το Render
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Chris Bet Bot is running!")

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

# Εντολή /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🤖 **Welcome to Chris Bet Bot!**\n\n"
        "Χρησιμοποιήστε τις παρακάτω εντολές:\n"
        "• /matches - Δείτε τα σημερινά ματς και τις προγνωστικές αναλύσεις\n"
        "• /help - Βοήθεια και πληροφορίες"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

# Εντολή /matches (με τα προγνωστικά και ποσοστά)
async def matches(update: Update, context: ContextTypes.DEFAULT_TYPE):
    matches_text = (
        "📊 **Προγνωστικά Αγώνων & Over/Under (90%+)**\n\n"
        "⚽ **Demo Match 1: Real Madrid vs Barcelona**\n"
        "• Επιλογή: Over 2.5 Goals\n"
        "• Ποσοστό Επιτυχίας: 92%\n"
        "• 1Χ2 Εκτίμηση: 1 (Άσος)\n\n"
        "⚽ **Demo Match 2: Arsenal vs Manchester City**\n"
        "• Επιλογή: Both Teams to Score (G/G)\n"
        "• Ποσοστό Επιτυχίας: 90%\n"
        "• 1Χ2 Εκτίμηση: X (Ισοπαλία)"
    )
    await update.message.reply_text(matches_text, parse_mode="Markdown")

if __name__ == '__main__':
    # Εκκίνηση του web server στο background
    threading.Thread(target=run_web_server, daemon=True).start()
    
    # Token του bot
    TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8968240612:AAHAxgelBq__DPW-m2NM3a3YEuMS7SMOMDw")
    
    # Δημιουργία του Telegram Bot
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("matches", matches))
    
    print("Chris Bet Bot started successfully...")
    app.run_polling()
