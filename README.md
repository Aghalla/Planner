<div dir="rtl">

# پلنر 📋

یک **Productivity Planner** فارسی، مدرن و کامل با جنگو — با تم Graphite + Orange، تقویم شمسی واقعی و کاملاً ریسپانسیو.

![Django](https://img.shields.io/badge/Django-6.1-green) ![Python](https://img.shields.io/badge/Python-3.12%2B-blue) ![License](https://img.shields.io/badge/License-MIT-orange)

## ✨ امکانات

| بخش | توضیح |
|---|---|
| 📊 داشبورد | Greeting هوشمند، تاریخ شمسی، ویجت‌های قابل شخصی‌سازی با Drag & Drop |
| 📝 کارها | اولویت، هدف، ساعت، ۳ کار اصلی روز (Today's Focus)، انتقال کار عقب‌افتاده به فردا |
| 🔥 عادت‌ها | استریک، درصد موفقیت، هیت‌مپ ۱۵ هفته اخیر |
| 🎯 اهداف | سلسله‌مراتبی (هدف ← زیرهدف ← کار) با نوار پیشرفت و موعد شمسی |
| 📅 تقویم | شمسی واقعی (شنبه تا جمعه)، نمای ماه/هفته/روز، رویداد و یادآوری |
| 🍅 پومودورو | تایمر با Progress Ring، اتصال به کار، زمان‌های قابل تنظیم، زنگ پایان |
| 📈 آمار | نمودار خطی تمرکز روزانه + تفکیک دقایق هر کار |
| ⚙️ تنظیمات | نام، اعلان‌ها، پومودورو و ظاهر |

## 🚀 اجرای سریع (ویندوز)

**قدم ۰ — کلون کردن ریپو:**
```bash
git clone https://github.com/Aghalla/Planner.git
cd Planner
```

**قدم ۱ — نصب خودکار** (فقط بار اول بعد از کلون):
```
دابل‌کلیک روی Setup.bat
```
این فایل خودش محیط مجازی می‌سازه، پکیج‌ها رو نصب می‌کنه، مایگریشن می‌زنه و محتوای روزانه رو می‌سازه.

**قدم ۲ — اجرا:**
```
دابل‌کلیک روی Planner.bat
```
مرورگر روی `http://127.0.0.1:8000/` باز می‌شه. اول از صفحه ثبت‌نام یه حساب بساز.

## 🛠️ نصب دستی

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_content
python manage.py runserver
```

## 🧪 تست خودکار

```bash
python manage.py shell -c "exec(open('core/selftest.py', encoding='utf-8').read())"
```

## 🗂️ ساختار پروژه

```
Planner/
├── Planner.bat          # اجرای برنامه با یک کلیک
├── Setup.bat            # نصب خودکار محیط بعد از کلون
├── requirements.txt
├── manage.py
├── core/
│   ├── models.py        # Task, Habit, Goal, Event, Pomodoro, Settings, ...
│   ├── views.py         # ویوها + APIهای JSON
│   ├── urls.py
│   ├── jalali_utils.py  # موتور شمسی داخلی (بدون وابستگی خارجی)
│   ├── static/css/      # تم Graphite & Orange
│   └── static/js/       # jalali.js (دیت‌پیکر شمسی)، forms.js (مودال‌ها)، main.js
├── templates/           # قالب‌های فارسی RTL
└── Planner/             # تنظیمات جنگو
```

## 📝 نکات

- دیتابیس SQLite هست (`db.sqlite3`) و توی گیت ignore شده — هرکس با `Setup.bat` دیتابیس خودش رو می‌سازه.
- تقویم شمسی موتور داخلی داره (`jalali_utils.py`) و بدون `jdatetime` هم کار می‌کنه.
- تایم‌زون پیش‌فرض: `Asia/Tehran`.

## 📄 لایسنس

MIT

</div>
