<div dir="rtl">

# راهنمای آماده‌سازی محیط (Python) و (`.venv`)

## فعال‌سازی محیط مجازی

```bash
source .venv/bin/activate
```

اگر هنوز محیط (`.venv`) را نساخته‌اید:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

## آپدیت کردن (`pip`)

بعد از فعال کردن محیط مجازی بهتر است (`pip`) را آپدیت کنید:

```bash
python -m pip install --upgrade pip
```

---

## نصب کردن (`dependency`)‌ها داخل (`.venv`)

### نصب (`dependency`)‌های (`runtime`)

```bash
pip install -e .
```

### نصب (`dependency`)‌های (`runtime`) + (`dev`)

```bash
pip install -e ".[dev]"
```

---

این دستور خیلی مهم است، چون باعث می‌شود همه (`dependency`)‌ها داخل محیط مجازی (`.venv`) نصب شوند و پروژه درست اجرا شود.

</div>
