# 🤖 Raqamli Muharrir — Telegram Bot

## Bu bot nima qiladi?
- 📰 Kun.uz, Daryo.uz, BBC, Reuters, TechCrunch va boshqa saytlardan yangilik oladi
- 🌐 Avtomatik O'zbek tiliga tarjima qiladi
- 💱 Har kuni ertalab valyuta kurslarini yuboradi (CBU dan)
- 🌤 Har kuni ertalab ob-havo yuboradi
- ⏰ Kuniga 7 marta avtomatik post tashlaydi

---

## ⚡ QADAM-QADAM O'RNATISH

### 1-QADAM: Bot yaratish (5 daqiqa, bepul)
1. Telegramda **@BotFather** ga yozing
2. `/newbot` yuboring
3. Bot nomini kiriting: masalan `Raqamli Muharrir Bot`
4. Username kiriting: masalan `raqamli_muharrir_bot`
5. **TOKEN** beriladi — uni nusxalab oling (shunday ko'rinadi: `7123456789:AAHxxxxxxxx`)

### 2-QADAM: Botni kanalga qo'shish
1. Kanalingiz sozlamalariga o'ting
2. **Administrators → Add Administrator**
3. Botni topib, qo'shing
4. Barcha huquqlarni bering (Post messages, Edit messages)

### 3-QADAM: Ob-havo API (5 daqiqa, bepul)
1. https://openweathermap.org/api ga o'ting
2. Ro'yxatdan o'ting (bepul)
3. **API Keys** bo'limidan kalitni nusxalab oling

### 4-QADAM: bot.py faylini sozlash
`bot.py` faylini oching va quyidagilarni o'zgartiring:

```
BOT_TOKEN = "7123456789:AAHxxxxxxxx"   # 1-qadamda olingan token
CHANNEL_ID = "@raqamlimuharrir"        # Sizning kanal username
OPENWEATHER_API_KEY = "abc123..."      # 3-qadamda olingan kalit
```

### 5-QADAM: Railway.app ga joylashtirish ($5/oy)

1. **https://railway.app** ga o'ting
2. GitHub akkount bilan kiring
3. **New Project → Deploy from GitHub repo** bosing
4. Yangi repo yarating va ikkala faylni (bot.py, requirements.txt) yuklang
5. **Deploy** bosing
6. Bot 24/7 ishlaydi! ✅

---

## 📋 Bot nimalar yuboradi?

### Har kuni 08:00 — Valyuta kurslari:
```
💱 Bugungi valyuta kurslari
📅 21.04.2026

🇺🇸 1 USD = 12,750.00 so'm
🇪🇺 1 EUR = 13,900.00 so'm
🇷🇺 1 RUB = 142.00 so'm
```

### Har kuni 08:05 — Ob-havo:
```
🌤 Ob-havo | Toshkent
📅 21.04.2026

☀️ Harorat: 24°C
🌡 His etiladi: 22°C
☁️ Havo: ochiq osmon
💧 Namlik: 35%
💨 Shamol: 3 m/s
```

### Har 2 soatda — Yangilik:
```
💻 OpenAI yangi GPT-5 modelini taqdim etdi

Kompaniya yangi sun'iy intellekt modelini...

🔗 Batafsil o'qish →

#Texnologiya | 🕐 10:00 • 21.04.2026
```

---

## ❓ Muammolar bo'lsa

**Bot ishlamayapti?**
- TOKEN to'g'ri kiritilganini tekshiring
- Bot kanalga admin qilib qo'shilganini tekshiring

**Ob-havo kelayotgani yo'q?**
- OPENWEATHER_API_KEY ni tekshiring
- Yangi kalit faollashishi 10-30 daqiqa vaqt oladi

**Yordam kerakmi?**
- @raqamlimuharrir ga yozing

---

*Kod yozuvchi: Claude (Anthropic) | Bot egasi: Furkat*
