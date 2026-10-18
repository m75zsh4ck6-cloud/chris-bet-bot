import os
import logging
import requests
import xml.etree.ElementTree as ET
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
CHANNEL_USERNAME = os.environ.get("CHANNEL_USERNAME", "telegram")

# Πηγές RSS Feeds (Newsit)
RSS_FEEDS = {
    "LIFESTYLE": "https://www.newsit.gr/category/lifestyle/feed/",
    "NEWS": "https://www.newsit.gr/category/ellada/feed/",
    "WORLD": "https://www.newsit.gr/category/kosmos/feed/"
}

DEFAULT_IMAGE = "https://images.unsplash.com/photo-1504711434969-e33886168f5c?q=80&w=1000&auto=format&fit=crop"

def get_greece_time():
    """Επιστρέφει την τρέχουσα ώρα Ελλάδας."""
    try:
        return datetime.now(ZoneInfo("Europe/Athens"))
    except:
        return datetime.now()

def clean_html(text):
    """Αφαιρεί HTML tags από το κείμενο."""
    if not text:
        return ""
    cleanr = re.compile('<.*?>')
    return re.sub(cleanr, '', text).strip()

def fetch_rss_articles(category_key="LIFESTYLE", limit=4):
    """Τραβάει ζωντανά τις ειδήσεις με απλό HTTP Request & XML Parsing."""
    url = RSS_FEEDS.get(category_key, RSS_FEEDS["LIFESTYLE"])
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    try:
        response = requests.get(url, headers=headers, timeout=6)
        if response.status_code != 200:
            return []
            
        root = ET.fromstring(response.content)
        articles = []
        
        for item in root.findall('.//item')[:limit]:
            title = item.find('title').text if item.find('title') is not None else "Επικαιρότητα"
            link = item.find('link').text if item.find('link') is not None else "https://www.newsit.gr"
            desc_elem = item.find('description')
            summary = clean_html(desc_elem.text) if desc_elem is not None else ""
            
            if len(summary) > 110:
                summary = summary[:107] + "..."
                
            articles.append({
                "title": title,
                "link": link,
                "summary": summary
            })
            
        return articles
    except Exception as e:
        logging.error(f"Error reading RSS: {e}")
        return []

def format_news_caption(category_name, articles):
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
            msg += f"🔗 [Διαβάστε το άρθρο]({art['link']})\n\n"
    else:
        msg += "📌 **ΤΕΛΕΥΤΑΙΕΣ ΕΞΕΛΙΞΕΙΣ & ΕΙΔΗΣΕΙΣ**\n\n"
        msg += "🔴 **1. Συνεχής ενημέρωση για την επικαιρότητα**\n"
        msg += "🔗 [Διαβάστε όλες τις ειδήσεις στο Newsit](https://www.newsit.gr/)\n\n"
        msg += "🔴 **2. Lifestyle & Showbiz**\n"
        msg += "🔗 [Δείτε τα τελευταία ρεπορτάζ](https://www.newsit.gr/category/lifestyle/)\n\n"

    msg += "----------------------------------------\n"
    msg += "👇 *Πατήστε κατηγορία ή ανανεώστε τη ροή.*"
    return msg

async def send_news_feed(update: Update, context: ContextTypes.DEFAULT_TYPE, category_key="LIFESTYLE", category_name="LIFESTYLE & SHOWBIZ"):
    articles = fetch_rss_articles(category_key=category_key, limit=4)
    caption = format_news_caption(category_name, articles)
    
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
        await query.answer("🔄 Ανανέωση ειδήσεων...")
        await send_news_feed(update, context, category_key=cat_key, category_name=cat_name)

def main():
    if not TELEGRAM_BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN missing!")
        return

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(button_handler))

    print("Stable News Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
