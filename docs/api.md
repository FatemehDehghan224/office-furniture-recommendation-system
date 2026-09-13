# API v1

مستندات تعاملی Swagger در `/api/docs/` و فایل OpenAPI در `/api/schema/` در دسترس‌اند.

## ایجاد پیشنهاد

`POST /api/v1/recommendations/`

```json
{
  "person": "manager",
  "productType": "office desk",
  "number_of_person": 1,
  "budget": 15000000,
  "style": "modern",
  "color": "white",
  "body_material": "wood",
  "top_k": 5
}
```

به‌جای `budget` می‌توان `budget_min` و `budget_max` را با هم ارسال کرد. مقدار `top_k` بین ۱ تا ۲۰ است و پیش‌فرض آن ۵ است.

## سایر مسیرها

- `POST /api/v1/chat/`: تبدیل یک پیام فارسی به state ساخت‌یافته؛ در صورت کامل‌شدن اطلاعات، پیشنهادها را نیز برمی‌گرداند. حداکثر ۲۰ پیام اخیر را می‌توان در `history` ارسال کرد.
- `GET /api/v1/products/`: فهرست صفحه‌بندی‌شدهٔ محصولات فعال؛ فیلترهای `person`، `productType`، `style` و `color` را می‌پذیرد.
- `GET /api/v1/recommendation-requests/{request_id}/`: نتیجهٔ ذخیره‌شدهٔ یک درخواست.
- `POST /api/v1/recommendation-requests/{request_id}/feedback/`: ثبت `was_helpful` و `comment`.
- `GET /health/`: بررسی اتصال برنامه و دیتابیس.
