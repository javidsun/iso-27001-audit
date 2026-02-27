# ISO-27001-AUDIT — Keycloak (Dev) Setup & Troubleshooting (Docker Compose)

> زبان: فارسی  
> هدف: مستندسازی کامل تست‌ها، علت انجام هر تست، مشکلاتی که پیش آمد، و روش حل آن‌ها — همراه با تمام فرمان‌ها (commands).

---

## 0) پیش‌نیازها و فرضیات

### سرویس‌ها (نام کانتینرها در Compose شما)
- `iso-audit-keycloak` → Keycloak (Quarkus)
- `iso-audit-keycloak-db` → Postgres مخصوص Keycloak
- `iso-audit-backend` → FastAPI (روی `:8003`)
- `iso-audit-db` → Postgres مخصوص Backend
- `iso-audit-toolbox` → کانتینر ابزار برای اجرای `curl` داخل network

### پورت‌ها
- Keycloak App: داخل شبکه Docker روی `http://keycloak:8080`
- Management / Health (Quarkus): روی `http://keycloak:9000`

> نکته: خیلی از endpointهای health روی پورت **9000** هستند، نه 8080.

---

## 1) چرا این تست‌ها را انجام دادیم؟

هدف تست‌ها این بود که مطمئن شویم:

1) **Backend بالا می‌آید و سالم است**  
2) **Keycloak بالا می‌آید و سالم است** (health)  
3) **Realm پروژه** واقعاً وجود دارد (`iso-audit`)  
4) **OIDC discovery** کار می‌کند (well-known)  
5) **Token** می‌توان گرفت (Resource Owner Password Grant در dev)  
6) **userinfo** با access token کار می‌کند (scope صحیح)  
7) **تنظیمات realm** (token lifetime, brute force, password policy) بعد از restart هم پایدار می‌ماند  
8) مشکل‌های رایج: import، permission، password policy، scope، port conflict، و … را پیدا و رفع کنیم

---

## 2) مرحله 1 — ریست کامل محیط (اختیاری ولی مفید)

وقتی شک می‌کنی state خراب شده، بهترین کار در dev اینه:

```bash
docker compose down -v
docker compose up --build
```

- `-v` تمام volumeها را پاک می‌کند (DBها هم پاک می‌شوند).
- برای اینکه realm import را از صفر ببینی، این کار کمک می‌کند.

---

## 3) مرحله 2 — کپی کردن realm_dev.json داخل Docker Volume (بدون mount host)

مشکل روی macOS Docker Desktop: mount فایل realm از host گاهی دردسر permission/paths می‌دهد. راه حل: **Docker volume + docker cp**

### 3.1) ساخت کانتینر موقت برای دسترسی به volume
```bash
docker run --rm -d --name kc-import \
  -v iso-27001-audit_keycloak_import:/import \
  alpine:3.20 sleep 999999
```

### 3.2) کپی فایل realm به داخل volume
(مسیر نمونه: `keycloak/realm/realm_dev.json`)
```bash
docker cp keycloak/realm/realm_dev.json kc-import:/import/realm_dev.json
```

### 3.3) بررسی اینکه فایل داخل volume هست
```bash
docker exec kc-import ls -la /import
```

### 3.4) خاموش کردن کانتینر موقت
```bash
docker stop kc-import
```

---

## 4) مرحله 3 — بررسی لاگ Keycloak و مشکل Permission در log file

### 4.1) لاگ‌ها
```bash
docker logs -f iso-audit-keycloak
```

### 4.2) خطای رایج
```
Failed to set log file
/opt/keycloak/.../data/log/keycloak.log (Permission denied)
```

#### معنی‌اش چیست؟
- Keycloak (Quarkus) می‌خواهد داخل `/opt/keycloak/data/log/` فایل بسازد/بنویسد
- ولی یا:
  - آن مسیر read-only شده
  - یا volume با owner/permissions نامناسب آمده
  - یا container با user غیر root اجرا می‌شود و حق نوشتن ندارد

#### راه‌حل‌های قابل قبول در dev
1) ساده‌ترین: **log را به stdout بفرست** (اصلاً file handler نداشته باش)
2) یا: volume/dir را با permission درست بساز (مثلاً با init container / chown)
3) یا: اصلاً mount `keycloak_logs` را حذف کن (در dev)

> نکته مهم: این خطا معمولاً جلوی بالا آمدن Keycloak را نمی‌گیرد، ولی noise ایجاد می‌کند.

---

## 5) مرحله 4 — فهمیدن اینکه health روی کدام پورت است

### مشکل
شما تست کردی:
- `http://keycloak:8080/health` و `.../health/ready`  
و جواب 404 گرفتی.

این طبیعی است، چون **health endpoint روی management interface** است:

### تست درست (داخل toolbox)
```bash
docker exec -it iso-audit-toolbox sh -lc 'curl -sS -i http://keycloak:9000/health/ready | head -n 60'
docker exec -it iso-audit-toolbox sh -lc 'curl -sS -i http://keycloak:9000/health/live  | head -n 60'
```

**انتظار**: `HTTP/1.1 200 OK` و JSON با `"status": "UP"`

---

## 6) مرحله 5 — تست Backend health

```bash
docker exec -it iso-audit-toolbox sh -lc \
'curl -fsS http://iso-audit-backend:8003/api/v1/health && echo OK'
```

**انتظار**:
```json
{"health":"OK"}OK
```

---

## 7) مرحله 6 — مطمئن شو realm وجود دارد (علت خطای 404 “Realm does not exist”)

وقتی realm import درست انجام نشده باشد:
- `/realms/iso-audit` می‌دهد 404
- و `.well-known` هم 404 می‌دهد

### تست realm
```bash
docker exec -it iso-audit-toolbox sh -lc \
'curl -i http://keycloak:8080/realms/iso-audit | head -n 20'
```

**انتظار**: `HTTP/1.1 200 OK`

### تست OIDC discovery
```bash
docker exec -it iso-audit-toolbox sh -lc \
'curl -fsS http://keycloak:8080/realms/iso-audit/.well-known/openid-configuration | head -c 300 && echo'
```

**انتظار**: JSON که شامل `issuer`, `token_endpoint`, ... باشد.

---

## 8) مرحله 7 — گرفتن token (password grant در dev)

### 8.1) تست token endpoint
```bash
docker exec -it iso-audit-toolbox sh -lc '
curl -sS -i -X POST http://keycloak:8080/realms/iso-audit/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=iso-audit-api" \
  -d "grant_type=password" \
  -d "username=javid" \
  -d "password=Admin@@00000" | head -n 40
'
```

**انتظار**:
- `HTTP/1.1 200 OK`
- JSON با `access_token`, `refresh_token`, `expires_in`

### 8.2) مشکل رایج: `invalid_grant` / `Account is not fully set up`
این وقتی رخ می‌دهد که برای کاربر:
- Required Actions فعال باشد (مثلاً Update Password)
- یا user مجبور باشد پروفایل را کامل کند
- یا policyها با وضعیت user clash داشته باشد

**رفع در dev**:
- در realm export مطمئن شو:
  - `temporary: false`
  - required actions برای user تنظیم نشده

---

## 9) مرحله 8 — تست userinfo و مشکل “Missing openid scope”

### 9.1) سناریوی شما
توکن گرفتی، ولی `/userinfo` داد:
```
403 Forbidden
WWW-Authenticate: ... insufficient_scope ... Missing openid scope
```

#### علت
`userinfo` طبق OIDC نیاز دارد scope شامل `openid` باشد.
اگر token request شما فقط `profile email` بدهد، userinfo گیر می‌کند.

### 9.2) تست کامل userinfo (استخراج token بدون jq)
```bash
docker exec -it iso-audit-toolbox sh -lc '
RESP=$(curl -sS -X POST http://keycloak:8080/realms/iso-audit/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=iso-audit-api" \
  -d "grant_type=password" \
  -d "username=javid" \
  -d "password=Admin@@00000" \
  -d "scope=openid profile email")

TOKEN=$(echo "$RESP" | tr -d "\n" | grep -o "\"access_token\":\"[^\"]*\"" | cut -d":" -f2- | tr -d "\"")
echo "TOKEN_LEN=${#TOKEN}"
[ -n "$TOKEN" ] || (echo "TOKEN_EMPTY" && echo "$RESP" && exit 1)

curl -sS -i http://keycloak:8080/realms/iso-audit/protocol/openid-connect/userinfo \
  -H "Authorization: Bearer $TOKEN" | head -n 80
'
```

**انتظار**: `HTTP/1.1 200 OK` و JSON اطلاعات user.

### 9.3) آیا می‌شود “مستقیم روی realm” ست کرد؟
بله — برای اینکه هر بار scope نفرستی:

در `realm_dev.json` داخل client:
- `defaultClientScopes` را ست کن (حداقل: `openid`, `profile`, `email`)

نمونه:

```json
{
  "clientId": "iso-audit-api",
  "enabled": true,
  "publicClient": true,
  "standardFlowEnabled": true,
  "directAccessGrantsEnabled": true,
  "redirectUris": ["http://localhost:*/*"],
  "webOrigins": ["+"],
  "defaultClientScopes": ["openid", "profile", "email"],
  "optionalClientScopes": ["roles", "web-origins", "offline_access"]
}
```

---

## 10) مرحله 9 — Password Policy و خطاهای مرتبط

### 10.1) Password Policy چیست؟
Password Policy یعنی قوانین حداقل امنیت رمز عبور برای کاربران realm:
- حداقل طول
- حروف بزرگ/کوچک
- عدد
- کاراکتر خاص
- ممنوعیت برابر بودن با username
- history (عدم استفاده مجدد از N رمز قبلی)

### 10.2) اشتباه رایج شما: رشته policy با سینتکس اشتباه
شما گذاشتی:
```json
"passwordPolicy": "length(12) and upperCase(1) and ..."
```
ولی Keycloak معمولاً policy را با **space-separated** و بدون `and` می‌خواهد.

نمونه صحیح (رایج):
```json
"passwordPolicy": "length(12) upperCase(1) lowerCase(1) digits(1) specialChars(1) notUsername passwordHistory(5)"
```

### 10.3) خطای `invalidPasswordMinLengthMessage`
این خطا معمولاً به یکی از این‌ها برمی‌گردد:
- مقدار policy invalid است (parse نمی‌شود)
- یا پیام ترجمه/کلید i18n مربوط به min length مشکل دارد (کمتر رایج)
- یا ترکیب policy باعث invalid state در startup import شده

**رفع سریع**:
- اول policy را ساده کن:
  - فقط `length(12)` را بگذار
- وقتی Keycloak بالا آمد، بعد policy را کامل‌تر کن.

---

## 11) مرحله 10 — Export realm و مشکل Port conflict (Address already in use)

شما هنگام `kc.sh export ...` دیدی:
```
Unable to start the management interface on 0.0.0.0:9000
Address already in use
```

#### علت
Keycloak کانتینر در حال اجراست و روی پورت 9000 نشسته.  
وقتی `kc.sh export` اجرا می‌کنی، بعضی مودها سعی می‌کنند management interface را بالا بیاورند و با پورت conflict می‌خورند.

**رفع**:
- یا قبل export کانتینر Keycloak را stop کن
- یا export را در کانتینر جدا با پورت متفاوت انجام بده
- یا از روش export/import مبتنی بر فایل/dir که در startup انجام می‌دهی استفاده کن

---

## 12) چک‌لیست نهایی (قبولی/رد)

### ✅ Pass
- Backend health:
  - `GET http://iso-audit-backend:8003/api/v1/health` → 200
- Keycloak health:
  - `GET http://keycloak:9000/health/ready` → 200
- Realm exists:
  - `GET http://keycloak:8080/realms/iso-audit` → 200
- Well-known works:
  - `GET .../.well-known/openid-configuration` → 200
- Token works:
  - `POST .../token` → 200 و access_token
- Userinfo works:
  - `GET .../userinfo` → 200 (با `openid` scope)

### ❌ Fail (علت‌های رایج)
- Realm missing → import انجام نشده یا فایل درست داخل `/opt/keycloak/data/import` نیست
- health روی 8080 → 404 (باید 9000)
- userinfo 403 insufficient_scope → scope شامل openid نیست
- startup crash invalidPasswordMinLengthMessage → passwordPolicy سینتکس غلط
- export crash Address already in use → 9000 در استفاده است

---

## 13) نمونه realm_dev.json (نسخه تمیز و قابل import)

> این نسخه را در مسیر repo نگه دار: `keycloak/realm/realm_dev.json`  
> سپس طبق مرحله 3 به volume import کپی کن.

```json
{
  "realm": "iso-audit",
  "enabled": true,
  "displayName": "ISO-27001 Audit (Dev)",

  "bruteForceProtected": true,
  "failureFactor": 5,
  "waitIncrementSeconds": 60,
  "minimumQuickLoginWaitSeconds": 60,
  "maxFailureWaitSeconds": 900,
  "quickLoginCheckMilliSeconds": 1000,
  "maxDeltaTimeSeconds": 43200,

  "accessTokenLifespan": 900,
  "ssoSessionIdleTimeout": 3600,
  "ssoSessionMaxLifespan": 28800,

  "passwordPolicy": "length(12) upperCase(1) lowerCase(1) digits(1) specialChars(1) notUsername passwordHistory(5)",

  "clients": [
    {
      "clientId": "iso-audit-api",
      "name": "ISO Audit API",
      "enabled": true,

      "publicClient": true,
      "standardFlowEnabled": true,
      "directAccessGrantsEnabled": true,

      "redirectUris": ["http://localhost:*/*"],
      "webOrigins": ["+"],

      "defaultClientScopes": ["openid", "profile", "email"],
      "optionalClientScopes": ["roles", "web-origins", "offline_access"]
    }
  ],

  "users": [
    {
      "username": "javid",
      "enabled": true,
      "emailVerified": true,
      "firstName": "Javid",
      "lastName": "Shamsi",
      "email": "javid@example.com",
      "credentials": [
        { "type": "password", "value": "Admin@@00000", "temporary": false }
      ]
    }
  ]
}
```

---

## 14) دستورهای سریع (Quick commands)

### Health
```bash
docker exec -it iso-audit-toolbox sh -lc 'curl -sS http://iso-audit-backend:8003/api/v1/health && echo OK'
docker exec -it iso-audit-toolbox sh -lc 'curl -sS http://keycloak:9000/health/ready && echo OK'
```

### Realm + Well-known
```bash
docker exec -it iso-audit-toolbox sh -lc 'curl -sS -i http://keycloak:8080/realms/iso-audit | head -n 10'
docker exec -it iso-audit-toolbox sh -lc 'curl -sS http://keycloak:8080/realms/iso-audit/.well-known/openid-configuration | head -c 250 && echo'
```

### Token + userinfo (با openid)
```bash
docker exec -it iso-audit-toolbox sh -lc '
RESP=$(curl -sS -X POST http://keycloak:8080/realms/iso-audit/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=iso-audit-api" \
  -d "grant_type=password" \
  -d "username=javid" \
  -d "password=Admin@@00000" \
  -d "scope=openid profile email")

TOKEN=$(echo "$RESP" | tr -d "\n" | grep -o "\"access_token\":\"[^\"]*\"" | cut -d":" -f2- | tr -d "\"")
curl -sS http://keycloak:8080/realms/iso-audit/protocol/openid-connect/userinfo \
  -H "Authorization: Bearer $TOKEN"
'
```

---

## 15) نکته‌ی مهم درباره “دو تا realm_dev.json”

### کدام فایل “مرجع” است؟
- **فایل داخل repo** (مثلاً `keycloak/realm/realm_dev.json`) → منبع اصلی (source of truth)
- فایل داخل volume import فقط **کپی runtime** است

پس:
1) فایل را در repo edit کن  
2) دوباره با `docker cp` داخل volume کپی کن  
3) Keycloak را restart کن تا import شود

---

### پایان
اگر خواستی این doc را کامل‌تر کنم (مثلاً شامل snippet از docker-compose مربوط به import dir/volume و health checks)، فایل compose خودت را بده.
