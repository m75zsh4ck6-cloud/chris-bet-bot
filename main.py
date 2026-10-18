import os
import logging
import feedparser
import re
from datetime import datetime
from zoneinfo import ZoneInfo
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHANNEL_USERNAME = os.environ.get("CHANNEL_USERNAME", "YourChannelUsername")

# Πηγές RSS για Πραγματικές Ειδήσεις & Lifestyle
RSS_FEEDS = {
    "LIFESTYLE": "https://www.protothema.gr/rss/lifestyle/",
    "NEWS": "https://www.protothema.gr/rss/greece/",
    "WORLD": "https://www.protothema.gr/rss/world/"
}

DEFAULT_IMAGE = "https://images.unsplash.com/photo-1504711434969-e33886168f5c?q=80&w=1000&auto=format&fit=crop"

def get_greece_time():
    """Επιστρέφει την τρέχουσα ώρα Ελλάδας."""
    try:
        return datetime.now(ZoneInfo("Europe/Athens"))
    except:
        return datetime.now()

def clean_html(raw_html):
    """Αφαιρεί HTML tags από τις περιλήψεις των RSS."""
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext.strip()

def fetch_real_news(category_key="LIFESTYLE", limit=4):
    """Τραβάει τις πραγματικές τελευταίες ειδήσεις από το αντίστοιχο RSS Feed."""
    feed_url = RSS_FEEDS.get(category_key, RSS_FEEDS["LIFESTYLE"])
    try:
        feed = feedparser.parse(feed_url)
        articles = []
        
        for entry in feed.entries[:limit]:
            title = entry.get("title", "Χωρίς τίτλο")
            link = entry.get("link", "#")
            summary = clean_html(entry.get("summary", entry.get("description", "")))
            
            # Μείωση μεγέθους περίληψης για να είναι ευανάγνωστη
            if len(summary) > 120:
                summary = summary[:117] + "..."
                
            articles.append({
                "title": title,
                "link": link,
                "summary": summary
            })
        return articles
    except Exception as e:
        logging.error(f"Error fetching RSS feed: {e}")
        return []

def format_news_message(category_name, articles):
    current_time_str = get_greece_time().strftime("%H:%M")
    current_date_str = get_greece_time().strftime("%d/%m/%Y")
    
    msg = f"✨ **LIVE NEWS HUB | {category_name}** 🌟\n"
    msg += f"📅 `{current_date_str}` | 🕒 Ώρα: `{current_time_str}`\n"
    msg += "----------------------------------------\n\n"
    
    if articles:
        for idx, art in enumerate(articles, start=1):
            msg += f"🔴 **{idx}. {art['title']}**\n"
            if art['summary']:
                msg += f"• _{art['summary']}_\n"
            msg += f"🔗 [Διαβάστε το πλήρες άρθρο]({art['link']})\n\n"
    else:
        msg += "ℹ️ Δεν ήταν δυνατή η φόρτωση των ειδήσεων αυτή τη στιγμή.\n\n"

    msg += "----------------------------------------\n"
    msg += "👇 *Επιλέξτε κατηγορία ή ανανεώστε τη ροή.*"
    return msg

async def send_news_feed(update: Update, context: ContextTypes.DEFAULT_TYPE, category_key="LIFESTYLE", category_name="LIFESTYLE & SHOWBIZ"):
    articles = fetch_real_news(category_key=category_key, limit=4)
    caption = format_news_message(category_name, articles)
    
    channel_url = f"https://t.me/{CHANNEL_USERNAME}"

    keyboard = [
        [
            InlineKeyboardButton("🌟 Lifestyle", callback_data="cat_LIFESTYLE"),
            InlineKeyboardButton("🇬🇷 Ελλάδα", callback_data="cat_NEWS"),
            InlineKeyboardButton("🌍 Κόσμος", callback_data="cat_WORLD")
        ],
        [InlineKeyboardButton("📢 Μπες στο Κανάλι μας", url=channel_url)],
        [InlineKeyboardButton("🔄 Ανανέωση Ειδήσεων", callback_data=f"refresh_{category_key}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_photo(
            photo=DEFAULT_IMAGE,
            caption=caption,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
    elif update.callback_query:
        try:
            await update.callback_query.message.edit_caption(
                caption=caption,
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
        except Exception:
            pass

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_news_feed(update, context, category_key="LIFESTYLE", category_name="LIFESTYLE & SHOWBIZ")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    if data.startswith("cat_"):
        cat_key = data.replace("cat_", "")
        names = {
            "LIFESTYLE": "LIFESTYLE & SHOWBIZ",
            "NEWS": "ΕΛΛΑΔΑ & ΕΠΙΚΑΙΡΟΤΗΤΑ",
            "WORLD": "ΔΙΕΘΝΗ ΝΕΑ"
        }
        cat_name = names.get(cat_key, "ΕIΔΗΣΕΙΣ")
        await query.answer(f"Φόρτωση: {cat_name}...")
        await send_news_feed(update, context, category_key=cat_key, category_name=cat_name)

    elif data.startswith("refresh_"):
        cat_key = data.replace("refresh_", "")
        names = {
            "LIFESTYLE": "LIFESTYLE & SHOWBIZ",
            "NEWS": "ΕΛΛΑΔΑ & ΕΠΙΚΑΙΡΟΤΗΤΑ",
            "WORLD": "ΔΙΕΘΝΗ ΝΕΑ"
        }
        cat_name = names.get(cat_key, "ΕIΔΗΣΕΙΣ")
        await query.answer("🔄 Ανανέωση τελευταίων ειδήσεων...")
        await send_news_feed(update, context, category_key=cat_key, category_name=cat_name)

def main():
    if not TELEGRAM_BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN missing!")
        return

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(button_handler))

    print("Real Live RSS News Bot is running successfully...")
    application.run_polling()

if __name__ == "__main__":
    main()
