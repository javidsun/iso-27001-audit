# Frontend - SaaS Platform

## Tech Stack
- **React Native** + **TypeScript**
- **Expo SDK 52** (cross-platform: Web, Android, iOS)
- آماده برای اتصال به **Keycloak** (OIDC)

## ساختار پروژه
```
frontend/
├── App.tsx                    # Entry point
├── package.json
├── app.json                   # Expo config (dark mode)
├── tsconfig.json
├── babel.config.js
└── src/
    ├── screens/
    │   └── LoginScreen.tsx    # صفحه لاگین
    ├── components/
    │   └── TextInput.tsx      # کامپوننت input سفارشی
    ├── constants/
    │   └── theme.ts           # رنگ‌ها، spacing، فونت
    ├── types/
    │   └── auth.ts            # تایپ فرم لاگین
    └── services/              # (آماده برای auth service)
```

## نصب و اجرا

### 1. نصب dependencies
```bash
cd frontend
npm install
```

### 2. اجرا روی وب
```bash
npx expo start --web
```
مرورگر باز می‌شه روی `http://localhost:8081`

### 3. اجرا روی موبایل
```bash
npx expo start
```
با اپ **Expo Go** روی گوشی QR code رو اسکن کن.

## صفحه لاگین
- **Username** (اجباری)
- **Email** (اختیاری)
- **First Name** (اختیاری)
- **Last Name** (اختیاری)
- **دکمه Sign In**

طراحی تاریک (Dark mode) با کادر مرکزی و outline آبی کرومی.

## اتصال به بک‌اند
- فعلاً لاگین mock هست (`TODO` در `LoginScreen.tsx`)
- برای اتصال به Keycloak، باید `handleLogin` در `LoginScreen.tsx` آپدیت بشه
- پورت بک‌اند: `8003` | Keycloak: `9000` | Frontend: `8081`

## نکات
- تداخلی با Docker Compose (`iso-27001-audit/`) نداره
- هر سه خروجی (Web, Android, iOS) از یک codebase هست
