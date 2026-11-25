# Universal Media

Universal Media — Telegram uchun o‘zbek, rus va ingliz tillarida ishlaydigan bepul, reklamasiz media va musiqa yordamchisi.

## Hozirgi kod imkoniyatlari

- aiogram 3 Telegram bot va FastAPI `/health` endpoint'i;
- O‘zbek, rus va ingliz tillarida interfeys;
- foydalanuvchi tili va faolligini PostgreSQL'da saqlash;
- shaxsiy chat va guruh chatlarini qayd etish;
- `/start`, `/help`, `/language`, `/music`, `/lyrics`, `/cancel` buyruqlari;
- Instagram, YouTube, TikTok va Pinterest HTTPS havolalarini xavfsiz host allowlist orqali aniqlash;
- Apple iTunes katalogidan qo‘shiq nomi yoki ijrochi bo‘yicha qidirish;
- ixtiyoriy Musixmatch API orqali qo‘shiq matnidan qisqa parcha bilan qidirish; faqat qo‘shiq metadata va rasmiy havola qaytariladi;
- ixtiyoriy AudD integratsiyasi orqali audio/voice/video ichidan musiqa tanish;
- video ichidan audioni ajratish uchun FFmpeg;
- so‘rovlar tezligini cheklash, foydalanuvchini bloklash va admin statistikasi;
- admin buyruqlari: `/admin`, `/users`, `/requests`, `/block ID`, `/unblock ID`;
- GitHub Actions orqali Python compile va unit testlar.

## Maxfiylik va saqlanadigan ma’lumotlar

- Bot ishlashi uchun foydalanuvchining Telegram ID, ism, username va tanlangan tili; chat ID va guruh nomi; so‘rov turi, holati va vaqti PostgreSQL’da saqlanadi.
- Bot qidiruv so‘rovlarining matnini va yuborilgan media fayllarni o‘z bazasida saqlamaydi.
- Audio tanish uchun audio AudD’ga, qo‘shiq matnidan qidirish uchun yuborilgan qisqa parcha Musixmatch’ga uzatiladi. Qo‘shiq nomi/ijrochi qidiruvi Apple katalogiga yuboriladi.
- Hozir foydalanuvchi ma’lumotlarini bot ichidan o‘chirish buyrug‘i yo‘q. Ommaviy ishga tushirishdan oldin ma’lumotlarni saqlash muddati, o‘chirish tartibi va maxfiylik siyosatini belgilash kerak.

## Muhim cheklovlar

- Media havolasi funksiyasi hozircha platformani aniqlaydi va foydalanuvchiga rasmiy manbaga qaytish havolasini beradi. Instagram, YouTube, TikTok yoki Pinterest kontentini yuklab olish funksiyasi yo‘q.
- Musiqa nomi/ijrochi qidiruvi Apple katalogidan metadata va rasmiy tinglash havolasini qaytaradi; audio nusxasini tarqatmaydi.
- Matn bo‘yicha qidiruv uchun `MUSIXMATCH_API_KEY` kerak. Foydalanuvchi yuborgan qisqa parcha qidiruv uchun Musixmatch API’ga yuboriladi; bot to‘liq qo‘shiq matnini saqlamaydi yoki qayta ko‘rsatmaydi.
- Ovozli xabar, audio va videodan musiqa aniqlash uchun alohida AudD API tokeni kerak. Tanib olish so‘rovida media fayl AudD xizmatiga yuboriladi; token bo‘lmasa, funksiya ishlamaydi. Foydalanuvchilarga bu haqda oldindan xabar berish kerak.
- DRM, login, paywall yoki platforma himoyalarini chetlab o‘tish rejalashtirilmagan. Audio tarqatish faqat tegishli litsenziya/ruxsat mavjud bo‘lganda ko‘rib chiqiladi.
- Hozirgi Render rejimi bitta web service instance va long polling uchun mo‘ljallangan. Bir nechta instance ishga tushirilsa, Telegram polling to‘qnashuvi yuz berishi mumkin.

## Mahalliy ishga tushirish

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
- `DATABASE_URL` — PostgreSQL ulanish manzili;
- `AUDD_API_TOKEN` — ixtiyoriy, audio orqali musiqa aniqlash uchun;
- `MUSIXMATCH_API_KEY` — ixtiyoriy, qo‘shiq matnidan qidirish uchun.

5. Ishga tushiring:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Tekshirish: `http://localhost:8000/health`.

## Telegram guruh sozlamasi

Bot guruhdagi oddiy xabarlar va havolalarni ko‘rishi uchun BotFather’da `/setprivacy` buyrug‘ini ochib, bot uchun Privacy Mode’ni `Disable` qiling. So‘ng botni guruhga qayta qo‘shing. Keraksiz administrator huquqlarini bermang. Privacy Mode yoqilgan bo‘lsa, Telegram oddiy guruh xabarlarini botga yubormasligi mumkin.

## Render

Render'da Blueprint orqali `render.yaml` ni tanlang. Hozirgi Blueprint web service uchun plan ko‘rsatilmagan: yangi Render web service uchun standart plan pullik `0.5c-512mb`; PostgreSQL esa `basic-256mb` planida yaratiladi. Bu loyiha foydalanuvchilar uchun bepul va reklamasiz bo‘lishi mumkin, ammo hostingning o‘zi bepul emas. Render narxlari o‘zgarishi mumkin; deploydan oldin Dashboard'da yakuniy narxni tekshiring. Free web service 15 daqiqa kiruvchi trafik bo‘lmasa uxlaydi, Free PostgreSQL esa 30 kundan keyin tugaydi, shuning uchun 24/7 bot uchun free rejim mos emas.

Web service va PostgreSQL yaratilgach, Environment bo‘limida `BOT_TOKEN` va `ADMIN_ID` ni kiriting. Audio tanish kerak bo‘lsa, `AUDD_API_TOKEN` ni; matn bo‘yicha qidirish kerak bo‘lsa, `MUSIXMATCH_API_KEY` ni ham kiriting. Haqiqiy tokenlarni GitHub'ga yoki chatga joylamang.

Render service uchun bitta instance ishlating. `/health` endpoint'i PostgreSQL va Telegram polling holatini tekshiradi.

## Testlar

GitHub Actions workflow Python fayllarini kompilyatsiya qiladi va `unittest` testlarini bajaradi. Testlar o‘tishi bot tashqi API kalitlari bilan jonli ishlayotganini anglatmaydi; deploydan oldin Telegram va provider bilan alohida sinov zarur.
