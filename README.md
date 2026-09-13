# Office Furniture Recommender

این برنامهٔ خط فرمان، نیاز کاربر را به فارسی دریافت می‌کند و محصولات مبلمان اداری را بر اساس نقش، نوع محصول، ظرفیت، بودجه و ترجیحات ظاهری رتبه‌بندی می‌کند. اگر تطابق کامل وجود نداشته باشد، منطق امتیازدهی نزدیک‌ترین گزینه‌ها را پیشنهاد می‌دهد.

## اجرای پروژه در ویندوز

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item recommendation\.env.example recommendation\.env
# سپس مقدار OPENAI_API_KEY را در recommendation\.env وارد کنید
python -m recommendation.main
```

کلید باید مربوط به AvalAI و قابل استفاده با API سازگار با OpenAI باشد. دادهٔ اصلی محصولات در `recommendation/data/sofa.json` است.

پوشهٔ `tests` یک نمونهٔ آزمایشی قدیمی است و نقطهٔ اجرای پروژه نیست.

## تست هستهٔ پیشنهاددهی

```powershell
python -m unittest recommendation.tests.test_golden_recommender -v
```

## اجرای API جنگو

```powershell
python manage.py migrate
python manage.py import_products
python manage.py runserver
```

پس از اجرا، API پیشنهاددهی در `http://127.0.0.1:8000/api/v1/recommendations/` و پنل مدیریت در `http://127.0.0.1:8000/admin/` در دسترس هستند. جزئیات معماری، API و ادامهٔ مسیر در پوشهٔ `docs` قرار دارد.
