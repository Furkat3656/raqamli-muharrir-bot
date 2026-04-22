#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════╗
║   RAQAMLI MUHARRIR - Avtomatik Bot       ║
║   Yangiliklar, Valyuta, Ob-havo          ║
╚══════════════════════════════════════════╝
"""

import feedparser
import requests
import schedule
import time
import json
import os
import random
import logging
import re
import html
from datetime import datetime, timezone, timedelta
from deep_translator import GoogleTranslator
import telebot

# ============================================================
#  ⚙️  SOZLAMALAR
# ============================================================

BOT_TOKEN = "8734825272:AAFKt7sJyrQ78FZQfduf8NaM4_sZ7mvGmdI"
CHANNEL_ID = "@raqamlimuharrir"

OPENWEATHER_API_KEY = "WEATHER_API_KEY"
CITY = "Tashkent"

POSTS_PER_DAY = 15
CHANNEL_USERNAME = "@raqamlimuharrir"

# O'zbekiston vaqt zonasi (UTC+5)
UZB_TZ = timezone(timedelta(hours=5))

# ============================================================
#  📡  YANGILIK MANBALARI (RSS)
# ============================================================

RSS_FEEDS = [
    {"url": "https://kun.uz/rss",                               "emoji": "🇺🇿", "cat": "Ozbekiston"},
    {"url": "https://daryo.uz/feed/",                           "emoji": "🇺🇿", "cat": "Ozbekiston"},
    {"url": "https://gazeta.uz/uz/rss/",                        "emoji": "🇺🇿", "cat": "Ozbekiston"},
    {"url": "https://feeds.bbci.co.uk/news/world/rss.xml",     "emoji": "🌍", "cat": "Jahon"},
    {"url": "https://rss.reuters.com/reuters/worldNews",        "emoji": "🌍", "cat": "Jahon"},
    {"url": "https://feeds.bbci.co.uk/news/rss.xml",           "emoji": "🌍", "cat": "Jahon"},
    {"url": "https://techcrunch.com/feed/",                     "emoji": "💻", "cat": "Texnologiya"},
    {"url": "https://feeds.feedburner.com/venturebeat/SZYF",   "emoji": "🤖", "cat": "AI"},
    {"url": "https://www.artificialintelligence-news.com/feed/","emoji": "🤖", "cat": "AI"},
    {"url": "https://feeds.bbci.co.uk/news/business/rss.xml",  "emoji": "💰", "cat": "Biznes"},
    {"url": "https://rss.reuters.com/reuters/businessNews",     "emoji": "💰", "cat": "Biznes"},
    {"url": "https://feeds.bbci.co.uk/sport/rss.xml",          "emoji": "⚽", "cat": "Sport"},
    {"url": "https://www.espn.com/espn/rss/news",              "emoji": "🏆", "cat": "Sport"},
]

# ============================================================
#  🔧  ASOSIY KOD
# ============================================================

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(BOT_TOKEN)
translator = GoogleTranslator(source='auto', target='uz')
POSTED_FILE = "posted_ids.json"


def now_uzb():
    """O'zbekiston vaqtini qaytarish (UTC+5)"""
    return datetime.now(UZB_TZ)


def clean_text(text: str) -> str:
    """HTML teglar va maxsus belgilarni tozalash"""
    if not text:
        return ""
    text = html.unescape(text)          # &laquo; &raquo; &nbsp; → oddiy belgi
    text = re.sub(r'<[^>]+>', '', text) # HTML teglarni o'chirish
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def load_posted():
    if os.path.exists(POSTED_FILE):
        with open(POSTED_FILE, 'r') as f:
            return set(json.load(f))
    return set()


def save_posted(posted: set):
    with open(POSTED_FILE, 'w') as f:
        json.dump(list(posted)[-1000:], f)


def safe_translate(text: str) -> str:
    try:
        if not text or len(text.strip()) < 5:
            return text
        text = clean_text(text)[:800]
        translated = translator.translate(text)
        if not translated:
            return text
        return clean_text(translated)
    except Exception as e:
        logger.warning(f"Tarjima xatosi: {e}")
        return text


def get_fresh_news():
    posted = load_posted()
    all_news = []

    for feed_info in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_info["url"])
            for entry in feed.entries[:8]:
                entry_id = entry.get('id') or entry.get('link', '')
                if entry_id and entry_id not in posted:
                    summary = entry.get('summary', '') or entry.get('description', '')
                    summary = clean_text(summary)[:400]
                    all_news.append({
                        "id": entry_id,
                        "title": clean_text(entry.get('title', '')),
                        "link": entry.get('link', ''),
                        "emoji": feed_info["emoji"],
                        "cat": feed_info["cat"],
                        "summary": summary,
                        "image": _get_image_from_entry(entry),
                    })
        except Exception as e:
            logger.error(f"RSS xatosi ({feed_info['url'][:40]}): {e}")

    logger.info(f"Jami {len(all_news)} ta yangi yangilik topildi")
    return all_news, posted


def _get_image_from_entry(entry):
    try:
        if hasattr(entry, 'media_content') and entry.media_content:
            return entry.media_content[0].get('url')
        if hasattr(entry, 'enclosures') and entry.enclosures:
            for enc in entry.enclosures:
                if 'image' in enc.get('type', ''):
                    return enc.get('href')
    except:
        pass
    return None


def get_currency_rates():
    try:
        r = requests.get("https://cbu.uz/uz/arkhiv-kursov-valyut/json/", timeout=10)
        data = r.json()
        rates = {}
        for item in data:
            if item['Ccy'] in ['USD', 'EUR', 'RUB', 'GBP', 'CNY']:
                rates[item['Ccy']] = float(item['Rate'])
        return rates
    except Exception as e:
        logger.error(f"Valyuta xatosi: {e}")
        return {}


def get_weather():
    try:
        url = (f"http://api.openweathermap.org/data/2.5/weather"
               f"?q={CITY}&appid={OPENWEATHER_API_KEY}&units=metric&lang=ru")
        r = requests.get(url, timeout=10)
        data = r.json()
        if data.get('cod') != 200:
            return None
        return {
            "temp": round(data['main']['temp']),
            "feels": round(data['main']['feels_like']),
            "desc": data['weather'][0]['description'],
            "humidity": data['main']['humidity'],
            "wind": data['wind']['speed'],
        }
    except Exception as e:
        logger.error(f"Ob-havo xatosi: {e}")
        return None


# ============================================================
#  📤  POST YUBORISH
# ============================================================

def post_news():
    news_list, posted = get_fresh_news()
    if not news_list:
        logger.info("Yangi yangilik topilmadi...")
        return

    news = random.choice(news_list)
    title_uz = safe_translate(news['title'])
    summary_uz = safe_translate(news['summary']) if news['summary'] else ""
    now = now_uzb().strftime('%H:%M • %d.%m.%Y')

    text = f"{news['emoji']} <b>{title_uz}</b>\n\n"
    if summary_uz:
        text += f"{summary_uz}\n\n"
    text += (f"🔗 <a href='{news['link']}'>Batafsil o'qish →</a>\n\n"
             f"#{news['cat']} | 🕐 {now}\n"
             f"📢 {CHANNEL_USERNAME}")

    try:
        if news.get('image'):
            try:
                bot.send_photo(CHANNEL_ID, photo=news['image'], caption=text, parse_mode='HTML')
            except:
                bot.send_message(CHANNEL_ID, text, parse_mode='HTML', disable_web_page_preview=False)
        else:
            bot.send_message(CHANNEL_ID, text, parse_mode='HTML', disable_web_page_preview=False)
        posted.add(news['id'])
        save_posted(posted)
        logger.info(f"✅ Post yuborildi: {news['title'][:60]}")
    except Exception as e:
        logger.error(f"❌ Post xatosi: {e}")


def post_currency():
    rates = get_currency_rates()
    if not rates:
        return
    date_str = now_uzb().strftime('%d.%m.%Y')
    text = f"💱 <b>Bugungi valyuta kurslari</b>\n📅 {date_str}\n\n"
    for ccy, flag in {'USD': '🇺🇸', 'EUR': '🇪🇺', 'RUB': '🇷🇺', 'GBP': '🇬🇧', 'CNY': '🇨🇳'}.items():
        if ccy in rates:
            text += f"{flag} 1 {ccy} = <b>{rates[ccy]:,.2f} so'm</b>\n"
    text += f"\n🏦 Manba: Markaziy Bank\n📢 {CHANNEL_USERNAME}"
    try:
        bot.send_message(CHANNEL_ID, text, parse_mode='HTML')
        logger.info("✅ Valyuta yuborildi")
    except Exception as e:
        logger.error(f"❌ Valyuta xatosi: {e}")


def post_weather():
    w = get_weather()
    if not w:
        return
    date_str = now_uzb().strftime('%d.%m.%Y')
    temp_emoji = "🔥" if w['temp'] >= 30 else "☀️" if w['temp'] >= 20 else "🌤" if w['temp'] >= 10 else "🌥" if w['temp'] >= 0 else "❄️"
    text = (f"🌤 <b>Ob-havo | Toshkent</b>\n📅 {date_str}\n\n"
            f"{temp_emoji} Harorat: <b>{w['temp']}°C</b>\n"
            f"🌡 His etiladi: <b>{w['feels']}°C</b>\n"
            f"☁️ Havo: {w['desc']}\n"
            f"💧 Namlik: <b>{w['humidity']}%</b>\n"
            f"💨 Shamol: <b>{w['wind']} m/s</b>\n\n"
            f"📢 {CHANNEL_USERNAME}")
    try:
        bot.send_message(CHANNEL_ID, text, parse_mode='HTML')
        logger.info("✅ Ob-havo yuborildi")
    except Exception as e:
        logger.error(f"❌ Ob-havo xatosi: {e}")


# ============================================================
#  ⏰  JADVAL (Railway UTC da ishlaydi → -5 soat)
# ============================================================

def setup_schedule():
    schedule.every().day.at("03:00").do(post_currency)  # 08:00 UZB
    schedule.every().day.at("03:05").do(post_weather)   # 08:05 UZB

    # 15 ta yangilik — UTC vaqtida (UZB = UTC+5)
    news_times_utc = [
        "03:30",  # 08:30 UZB
        "04:30",  # 09:30 UZB
        "05:30",  # 10:30 UZB
        "06:30",  # 11:30 UZB
        "07:30",  # 12:30 UZB
        "08:30",  # 13:30 UZB
        "09:30",  # 14:30 UZB
        "10:30",  # 15:30 UZB
        "11:30",  # 16:30 UZB
        "12:30",  # 17:30 UZB
        "13:30",  # 18:30 UZB
        "14:30",  # 19:30 UZB
        "15:30",  # 20:30 UZB
        "16:30",  # 21:30 UZB
        "17:30",  # 22:30 UZB
    ]
    for t in news_times_utc:
        schedule.every().day.at(t).do(post_news)

    logger.info("📅 Jadval tayyor (O'zbekiston vaqti):\n"
                "   💱 Valyuta: 08:00 | 🌤 Ob-havo: 08:05\n"
                "   📰 Yangiliklar: 08:30 dan 22:30 gacha (har soatda)")


# ============================================================
#  🚀  ISHGA TUSHIRISH
# ============================================================

if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("🤖 RAQAMLI MUHARRIR BOTI ISHGA TUSHDI!")
    logger.info(f"📢 Kanal: {CHANNEL_ID}")
    logger.info(f"🕐 O'zbekiston vaqti: {now_uzb().strftime('%H:%M • %d.%m.%Y')}")
    logger.info("=" * 50)

    setup_schedule()

    logger.info("📤 Test postlar yuborilmoqda...")
    post_currency()
    time.sleep(3)
    post_weather()
    time.sleep(3)
    post_news()

    logger.info("✅ Bot ishlayapti!")

    while True:
        schedule.run_pending()
        time.sleep(60)
