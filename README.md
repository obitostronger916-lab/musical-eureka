# Universal Media

Universal Media — Telegram uchun o‘zbek, rus va ingliz tillarida ishlaydigan media va musiqa yordamchisi.

## Hozirgi imkoniyatlar

- aiogram 3 Telegram bot va FastAPI `/health` endpoint'i;
- O‘zbek, rus va ingliz tillarida interfeys;
- foydalanuvchi tilini PostgreSQL'da saqlash;
- `/start`, `/language` va `/admin` buyruqlari;
- Apple iTunes katalogidan qo‘shiq nomi yoki ijrochi bo‘yicha qidirish;
- natijalarda qo‘shiq, ijrochi, albom ma’lumoti va rasmiy Apple Store havolasi.

Musiqa qidiruvi Apple iTunes Search API'dan metadata oladi. Bot audio fayl yoki preview yuklab bermaydi; foydalanuvchini rasmiy katalog sahifasiga yo‘naltiradi. Apple Search API qoidalariga muvofiq natijalar Apple Store kontentini targ‘ib qiluvchi havolalar bilan ko‘rsatiladi.

## Keyingi bosqichlar

Instagram, YouTube, TikTok va Pinterest havolalarini aniqlash; audio/ovoz/video orqali musiqa tanish; guruhlar uchun moderatsiya; kengaytirilgan admin paneli. Himoyalangan yoki ruxsatsiz kontentni yuklab olish funksiyasi rejalashtirilmagan.

## Ishga tushirish

1. Python 3.12 va PostgreSQL tayyorlang.
2. Repository'ni yuklab oling.
3. Virtual muhit yarating va kutubxonalarni o‘rnating:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows PowerShell:

```powershell
.venv\\Scripts\\Activate.ps1
```

4. `.env.example` faylidan `.env` nusxa yarating va quyidagilarni to‘ldiring:

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

## Tekshiruv

GitHub Actions workflow Python fayllarini kompilyatsiya qiladi va `unittest` testlarini bajaradi. Workflow natijasi hali tasdiqlanmagan bo‘lsa, loyiha sinovdan to‘liq o‘tgan deb hisoblanmaydi.

## Mas'uliyatli foydalanish

Bot faqat ommaviy yoki foydalanuvchi foydalanish huquqiga ega bo‘lgan kontent bilan ishlashi kerak. DRM, kirish cheklovlari yoki platforma himoyalarini chetlab o‘tish rejalashtirilmagan. Audio fayllarni tarqatish faqat tegishli ruxsat/litsenziya mavjud bo‘lganda qo‘shiladi.
