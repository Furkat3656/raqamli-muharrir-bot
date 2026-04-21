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
from datetime import datetime
from deep_translator import GoogleTranslator
import telebot

# ============================================================
#  ⚙️  SOZLAMALAR - FAQAT BU YERNI O'ZGARTIRING
# ============================================================

BOT_TOKEN = "8734825272:AAFKt7sJyrQ78FZQfduf8NaM4_sZ7mvGmdI"       # @BotFather dan olingan token
CHANNEL_ID = "@raqamlimuharrir"             # Kanal username yoki -100xxxxxxxxxx

OPENWEATHER_API_KEY = "WEATHER_API_KEY"     # openweathermap.org da bepul ro'yxatdan o'ting
CITY = "Tashkent"                           # Ob-havo qaysi shahar uchun

POSTS_PER_DAY = 7                           # Kuniga nechta yangilik (5-10)
CHANNEL_USERNAME = "@raqamlimuharrir"       # Post tagida ko'rinadigan kanal nomi

# ============================================================
#  📡  YANGILIK MANBALARI (RSS)
# ============================================================

RSS_FEEDS = [
    # --- O'ZBEKISTON ---
    {"url": "https://kun.uz/rss",                               "emoji": "🇺🇿", "cat": "Ozbekiston"},
    {"url": "https://daryo.uz/feed/",                           "emoji": "🇺🇿", "cat": "Ozbekiston"},
    {"url": "https://gazeta.uz/uz/rss/",                        "emoji": "🇺🇿", "cat": "Ozbekiston"},

    # --- JAHON ---
    {"url": "https://feeds.bbci.co.uk/news/world/rss.xml",     "emoji": "🌍", "cat": "Jahon"},
    {"url": "https://rss.reuters.com/reuters/worldNews",        "emoji": "🌍", "cat": "Jahon"},
    {"url": "https://feeds.bbci.co.uk/news/rss.xml",           "emoji": "🌍", "cat": "Jahon"},

    # --- TEXNOLOGIYA & AI ---
    {"url": "https://techcrunch.com/feed/",                     "emoji": "💻", "cat": "Texnologiya"},
    {"url": "https://feeds.feedburner.com/venturebeat/SZYF",   "emoji": "🤖", "cat": "AI"},
    {"url": "https://www.artificialintelligence-news.com/feed/","emoji": "🤖", "cat": "AI"},

    # --- BIZNES ---
    {"url": "https://feeds.bbci.co.uk/news/business/rss.xml",  "emoji": "💰", "cat": "Biznes"},
    {"url": "https://rss.reuters.com/reuters/businessNews",     "emoji": "💰", "cat": "Biznes"},

    # --- SPORT ---
    {"url": "https://feeds.bbci.co.uk/sport/rss.xml",          "emoji": "⚽", "cat": "Sport"},
    {"url": "https://www.espn.com/espn/rss/news",              "emoji": "🏆", "cat": "Sport"},
]

# ============================================================
#  🔧  ASOSIY KOD (O'ZGARTIRMANG)
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(BOT_TOKEN)
translator = GoogleTranslator(source='auto', target='uz')
POSTED_FILE = "posted_ids.json"


def load_posted():
    """Yuborilgan postlar ID larini yuklash"""
    if os.path.exists(POSTED_FILE):
        with open(POSTED_FILE, 'r') as f:
            return set(json.load(f))
    return set()


def save_posted(posted: set):
    """Yuborilgan postlarni saqlash (faqat oxirgi 1000 ta)"""
    with open(POSTED_FILE, 'w') as f:
        json.dump(list(posted)[-1000:], f)


def safe_translate(text: str) -> str:
    """Matnni o'zbek tiliga tarjima qilish"""
    try:
        if not text or len(text.strip()) < 5:
            return text
        text = text[:800]  # Uzun matnni qisqartirish
        translated = translator.translate(text)
        return translated if translated else text
    except Exception as e:
        logger.warning(f"Tarjima xatosi: {e}")
        return text


def get_fresh_news():
    """Barcha manbalardan yangi yangiliklar olish"""
    posted = load_posted()
    all_news = []

    for feed_info in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_info["url"])
            for entry in feed.entries[:8]:
                entry_id = entry.get('id') or entry.get('link', '')
                if entry_id and entry_id not in posted:
                    summary = entry.get('summary', '') or entry.get('description', '')
                    # HTML teglarini tozalash
                    import re
                    summary = re.sub(r'<[^>]+>', '', summary)[:400]

                    all_news.append({
                        "id": entry_id,
                        "title": entry.get('title', '').strip(),
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
    """Yangilikdan rasm URL ini olish"""
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
    """Markaziy bank valyuta kurslarini olish"""
    try:
        url = "https://cbu.uz/uz/arkhiv-kursov-valyut/json/"
        r = requests.get(url, timeout=10)
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
    """Toshkent ob-havo ma'lumotlarini olish"""
    try:
        url = (
            f"http://api.openweathermap.org/data/2.5/weather"
            f"?q={CITY}&appid={OPENWEATHER_API_KEY}&units=metric&lang=ru"
        )
        r = requests.get(url, timeout=10)
        data = r.json()
        if data.get('cod') != 200:
            return None
        temp = data['main']['temp']
        feels = data['main']['feels_like']
        desc = data['weather'][0]['description']
        humidity = data['main']['humidity']
        wind = data['wind']['speed']
        return {
            "temp": round(temp),
            "feels": round(feels),
            "desc": desc,
            "humidity": humidity,
            "wind": wind,
        }
    except Exception as e:
        logger.error(f"Ob-havo xatosi: {e}")
        return None


# ============================================================
#  📤  POST YUBORISH FUNKSIYALARI
# ============================================================

def post_news():
    """Yangilik postini yuborish"""
    news_list, posted = get_fresh_news()

    if not news_list:
        logger.info("Yangi yangilik topilmadi, keyingisini kutish...")
        return

    # Tasodifiy yangilik tanlash
    news = random.choice(news_list)

    # Tarjima
    title_uz = safe_translate(news['title'])
    summary_uz = safe_translate(news['summary']) if news['summary'] else ""

    # Post matni formatlash
    now = datetime.now().strftime('%H:%M • %d.%m.%Y')
    text = (
        f"{news['emoji']} <b>{title_uz}</b>\n\n"
    )
    if summary_uz:
        text += f"{summary_uz}\n\n"

    text += (
        f"🔗 <a href='{news['link']}'>Batafsil o'qish →</a>\n\n"
        f"#{news['cat']} | 🕐 {now}\n"
        f"📢 {CHANNEL_USERNAME}"
    )

    try:
        # Rasm bilan yoki rasmsiz yuborish
        if news.get('image'):
            try:
                bot.send_photo(
                    CHANNEL_ID,
                    photo=news['image'],
                    caption=text,
                    parse_mode='HTML'
                )
            except:
                # Rasm yuklanmasa, odatiy matn
                bot.send_message(CHANNEL_ID, text, parse_mode='HTML',
                                 disable_web_page_preview=False)
        else:
            bot.send_message(CHANNEL_ID, text, parse_mode='HTML',
                             disable_web_page_preview=False)

        posted.add(news['id'])
        save_posted(posted)
        logger.info(f"✅ Post yuborildi: {news['title'][:60]}")

    except Exception as e:
        logger.error(f"❌ Post yuborishda xato: {e}")


def post_currency():
    """Valyuta kurslari postini yuborish"""
    rates = get_currency_rates()
    if not rates:
        logger.warning("Valyuta ma'lumotlari olinmadi")
        return

    date_str = datetime.now().strftime('%d.%m.%Y')
    text = f"💱 <b>Bugungi valyuta kurslari</b>\n📅 {date_str}\n\n"

    flags = {'USD': '🇺🇸', 'EUR': '🇪🇺', 'RUB': '🇷🇺', 'GBP': '🇬🇧', 'CNY': '🇨🇳'}
    for ccy, flag in flags.items():
        if ccy in rates:
            text += f"{flag} 1 {ccy} = <b>{rates[ccy]:,.2f} so'm</b>\n"

    text += f"\n🏦 Manba: Markaziy Bank\n📢 {CHANNEL_USERNAME}"

    try:
        bot.send_message(CHANNEL_ID, text, parse_mode='HTML')
        logger.info("✅ Valyuta kurslari yuborildi")
    except Exception as e:
        logger.error(f"❌ Valyuta post xatosi: {e}")


def post_weather():
    """Ob-havo postini yuborish"""
    w = get_weather()
    if not w:
        logger.warning("Ob-havo ma'lumoti olinmadi")
        return

    date_str = datetime.now().strftime('%d.%m.%Y')

    # Haroratga qarab emoji
    if w['temp'] >= 30:
        temp_emoji = "🔥"
    elif w['temp'] >= 20:
        temp_emoji = "☀️"
    elif w['temp'] >= 10:
        temp_emoji = "🌤"
    elif w['temp'] >= 0:
        temp_emoji = "🌥"
    else:
        temp_emoji = "❄️"

    text = (
        f"🌤 <b>Ob-havo | Toshkent</b>\n📅 {date_str}\n\n"
        f"{temp_emoji} Harorat: <b>{w['temp']}°C</b>\n"
        f"🌡 His etiladi: <b>{w['feels']}°C</b>\n"
        f"☁️ Havo: {w['desc']}\n"
        f"💧 Namlik: <b>{w['humidity']}%</b>\n"
        f"💨 Shamol: <b>{w['wind']} m/s</b>\n\n"
        f"📢 {CHANNEL_USERNAME}"
    )

    try:
        bot.send_message(CHANNEL_ID, text, parse_mode='HTML')
        logger.info("✅ Ob-havo yuborildi")
    except Exception as e:
        logger.error(f"❌ Ob-havo post xatosi: {e}")


# ============================================================
#  ⏰  JADVAL SOZLASH
# ============================================================

def setup_schedule():
    """Kunlik jadval"""

    # Ertalabki paket (valyuta + ob-havo)
    schedule.every().day.at("08:00").do(post_currency)
    schedule.every().day.at("08:05").do(post_weather)

    # Yangiliklar vaqtlari (7 ta post)
    news_times = ["09:00", "10:30", "12:00", "14:00", "16:00", "18:30", "21:00"]
    for t in news_times[:POSTS_PER_DAY]:
        schedule.every().day.at(t).do(post_news)

    logger.info(
        f"📅 Jadval tayyor:\n"
        f"   💱 Valyuta: 08:00\n"
        f"   🌤 Ob-havo: 08:05\n"
        f"   📰 Yangiliklar: {', '.join(news_times[:POSTS_PER_DAY])}"
    )


# ============================================================
#  🚀  ISHGA TUSHIRISH
# ============================================================

if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("🤖 RAQAMLI MUHARRIR BOTI ISHGA TUSHDI!")
    logger.info(f"📢 Kanal: {CHANNEL_ID}")
    logger.info("=" * 50)

    setup_schedule()

    # Dastlabki test postlar
    logger.info("📤 Birinchi test postlar yuborilmoqda...")
    post_currency()
    time.sleep(3)
    post_weather()
    time.sleep(3)
    post_news()

    logger.info("✅ Test postlar yuborildi. Bot ishlayapti...")

    # Asosiy loop
    while True:
        schedule.run_pending()
        time.sleep(60)
