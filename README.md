# Universal Media

Universal Media — Telegram uchun o‘zbek, rus va ingliz tillarida ishlaydigan media va musiqa yordamchisi.

## Hozirgi bosqich

Repository'ga boshlang‘ich loyiha skeleti joylandi:
- aiogram 3 Telegram bot;
- Uzbek / Русский / English til tanlash;
- foydalanuvchi tilini PostgreSQL'da saqlash;
- /start, /language va /admin buyruqlari;
- FastAPI /health endpoint'i;
- Docker va Render konfiguratsiyasi.

Musiqa qidirish, media havolalarini tekshirish/qayta ishlash, audio orqali aniqlash, guruh moderatsiyasi va to‘liq admin paneli keyingi bosqichlarda ulanadi. Hozircha botni tayyor mahsulot deb hisoblamang.

## Ishga tushirish

1. Python 3.12 va PostgreSQL tayyorlang.
2. Repository'ni kompyuterga yuklab oling.
3. Virtual muhit yarating va kutubxonalarni o‘rnating:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows'da virtual muhitni faollashtirish:

```powershell
.venv\\Scripts\\Activate.ps1
```

4. `.env.example` faylidan `.env` nusxa yarating va qiymatlarni to‘ldiring:

- `BOT_TOKEN` — BotFather bergan bot tokeni;
- `ADMIN_ID` — asosiy administratorning raqamli Telegram ID'si;
- `DATABASE_URL` — PostgreSQL ulanish manzili.

5. Ishga tushiring:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Tekshirish: `http://localhost:8000/health`.

## Render

Render'da Blueprint orqali `render.yaml` ni tanlang. Web service va PostgreSQL yaratilgach, Environment bo‘limida `BOT_TOKEN` va `ADMIN_ID` ni kiriting. Haqiqiy tokenni GitHub'ga yoki chatga joylamang.

## Mas'uliyatli foydalanish

Bot faqat ommaviy yoki foydalanuvchi foydalanish huquqiga ega bo‘lgan kontent bilan ishlashi kerak. DRM, kirish cheklovlari yoki platforma himoyalarini chetlab o‘tish rejalashtirilmagan. Audio fayllarni tarqatish faqat tegishli ruxsat/litsenziya mavjud bo‘lganda qo‘shiladi.
