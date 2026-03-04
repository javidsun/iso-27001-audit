# JWT Validation Architecture Decision

# تصمیم معماری اعتبارسنجی JWT

------------------------------------------------------------------------

## 1️⃣ Context \| زمینه

### English

In the ISO-27001-Audit backend, authentication is handled using JWT
tokens issued by Keycloak. Incoming requests include:

Authorization: Bearer `<token>`{=html}

The architectural decision was made NOT to implement JWT validation as a
global HTTP middleware, but instead to use FastAPI's Dependency
Injection system.

### فارسی

در بک‌اند ISO-27001-Audit، احراز هویت با استفاده از توکن‌های JWT صادرشده
توسط Keycloak انجام می‌شود. درخواست‌های ورودی شامل هدر زیر هستند:

Authorization: Bearer `<token>`{=html}

تصمیم معماری این بود که اعتبارسنجی JWT به‌صورت Middleware سراسری
پیاده‌سازی نشود، بلکه از سیستم Dependency Injection در FastAPI استفاده
شود.

------------------------------------------------------------------------

## 2️⃣ What JWT Validation Does \| JWT دقیقاً چه کاری انجام می‌دهد

### English

When a request reaches the backend, the system must:

1.  Extract the Authorization header
2.  Parse the Bearer token
3.  Validate the signature using the JWKS endpoint
4.  Verify issuer (iss)
5.  Verify expiration (exp)
6.  Optionally verify audience (aud)
7.  Reject invalid tokens with 401 Unauthorized

This process must occur before business logic execution.

### فارسی

زمانی که درخواست به بک‌اند می‌رسد، سیستم باید:

1.  هدر Authorization را استخراج کند\
2.  توکن Bearer را تجزیه کند\
3.  امضا را از طریق JWKS بررسی کند\
4.  مقدار issuer (iss) را اعتبارسنجی کند\
5.  تاریخ انقضا (exp) را بررسی کند\
6.  در صورت نیاز audience (aud) را بررسی کند\
7.  در صورت نامعتبر بودن، پاسخ 401 Unauthorized برگرداند

این فرآیند باید قبل از اجرای منطق بیزینسی انجام شود.

------------------------------------------------------------------------

## 3️⃣ Option 1 --- Global Middleware \| گزینه اول: Middleware سراسری

### English Example

@app.middleware("http") async def jwt_middleware(request: Request,
call_next): token = extract_token(request) validate_token(token) return
await call_next(request)

### Problems \| مشکلات

### English

-   Applies to ALL routes (including /health)
-   Requires exclusions for public endpoints
-   Harder to manage RBAC
-   Reduces modularity and testability

### فارسی

-   روی تمام routeها اجرا می‌شود (حتی /health)\
-   نیاز به استثناء برای endpointهای عمومی دارد\
-   مدیریت Role-Based Access سخت‌تر می‌شود\
-   ماژولار بودن و تست‌پذیری کاهش می‌یابد

------------------------------------------------------------------------

## 4️⃣ Option 2 --- Dependency-Based Security (Chosen)

## گزینه دوم: امنیت مبتنی بر Dependency (انتخاب‌شده)

### English Example

def get_current_user(token: str = Depends(oauth2_scheme)):
validate_token(token) return decoded_payload

Usage:

@router.get("/secure") def
secure_endpoint(user=Depends(get_current_user)): return {"message":
"Protected content"}

### Advantages \| مزایا

### English

-   Applied only to protected endpoints
-   No need for public-route exceptions
-   Cleaner architecture
-   Easier RBAC extension
-   Better unit testing
-   Aligns with FastAPI best practices

### فارسی

-   فقط روی endpointهای محافظت‌شده اعمال می‌شود\
-   نیاز به شرط‌گذاری برای routeهای عمومی ندارد\
-   معماری تمیزتر ایجاد می‌کند\
-   افزودن RBAC آسان‌تر است\
-   تست واحد ساده‌تر می‌شود\
-   مطابق با Best Practice فریم‌ورک FastAPI است

------------------------------------------------------------------------

## 5️⃣ Architectural Justification \| توجیه معماری

### English

JWT validation is a cross-cutting concern. However, in FastAPI the
idiomatic way to implement authentication and authorization is through
Dependency Injection rather than global middleware.

Best Practice Mapping:

Logging → Middleware\
CORS → Middleware\
Authentication → Dependency\
Authorization → Dependency

### فارسی

اعتبارسنجی JWT یک Cross-Cutting Concern محسوب می‌شود. اما در FastAPI، روش
استاندارد و توصیه‌شده برای پیاده‌سازی احراز هویت و مجوزدهی، استفاده از
Dependency Injection است نه Middleware سراسری.

الگوی پیشنهادی:

Logging → Middleware\
CORS → Middleware\
Authentication → Dependency\
Authorization → Dependency

------------------------------------------------------------------------

## 6️⃣ Final Decision \| تصمیم نهایی

### English

JWT validation is implemented as a Dependency-based security layer to
ensure scalability, modularity, and future extensibility.

### فارسی

اعتبارسنجی JWT به‌صورت Dependency پیاده‌سازی شده است تا مقیاس‌پذیری،
ماژولار بودن و توسعه‌پذیری آینده تضمین شود.

------------------------------------------------------------------------

**Task Reference:** TASK-9.4 --- Backend API Client & JWT Validation
