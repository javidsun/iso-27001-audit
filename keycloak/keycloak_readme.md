# ISO-27001-AUDIT — Docker Compose + Keycloak (Dev) Cheat Sheet

## Obiettivo

- Avviare stack locale con:
  - Postgres per ISO audit
  - FastAPI backend (porta 8003)
  - Postgres separato per Keycloak
  - Keycloak su porta host **9000**
- Admin Keycloak: `admin_audit / admin123`
- Import realm da `realm_dev.json`
- Realm: `iso-audit`
- User: `javid / Javid123!`
- Evitare mount host (problemi macOS) usando **Docker volume + docker cp**

---

## 1) Avvio / Stop base

### Start (build backend + run tutto)

```bash
docker compose up --build
```

### Stop (senza cancellare volumi)

```bash
docker compose down
```

### Stop + rimozione volumi (ATTENZIONE: cancella anche DB)

```bash
docker compose down -v
```

---

## 2) Fix errori Docker (snapshot / build cache)

Se vedi errore tipo:

```
parent snapshot does not exist
```

Esegui:

```bash
docker compose down -v
docker builder prune -af
docker system prune -af --volumes
```

Poi:

```bash
docker compose build --no-cache
docker compose up
```

---

## 3) URL Accesso

### Keycloak

Home:

- `http://localhost:9000`

Admin Console:

- `http://localhost:9000/admin`

Admin login:

- `admin_audit`
- `admin123`

### Account Console (utente realm)

- `http://localhost:9000/realms/iso-audit/account`

User login:

- `javid`
- `Javid123!`

### Backend FastAPI

Health:

- `http://localhost:8003/api/v1/health`

---

## 4) Import Realm (senza mount host)

### Struttura file nel repo

- `keycloak/import/realm_dev.json`

### Esempio `realm_dev.json`

```json
{
  "id": "iso-audit",
  "realm": "iso-audit",
  "enabled": true,
  "users": [
    {
      "username": "javid",
      "enabled": true,
      "emailVerified": true,
      "credentials": [
        { "type": "password", "value": "Javid123!", "temporary": false }
      ]
    }
  ]
}
```

### Copiare il realm nel container

```bash
docker cp keycloak/import/realm_dev.json iso-audit-keycloak:/opt/keycloak/data/import/realm_dev.json
```

Riavvia Keycloak:

```bash
docker compose restart keycloak
```

Verifica import nei log:

```bash
docker logs iso-audit-keycloak | tail -n 200
```

---

## 5) Reset SOLO DB Keycloak (se import non funziona)

⚠️ Non tocca il DB ISO audit.

Stop:

```bash
docker compose down
```

Trova volume:

```bash
docker volume ls | grep keycloak_pgdata
```

Rimuovi volume (esempio):

```bash
docker volume rm iso-27001-audit_keycloak_pgdata
```

Riavvia:

```bash
docker compose up -d
```

Ricopia realm + restart Keycloak.

---

## 6) Accedere al DB Keycloak

Entrare nel container Postgres:

```bash
docker exec -it iso-audit-keycloak-db sh
```

Entrare in psql:

```bash
psql -U admin_audit -d keycloak
```

Mostrare tabelle:

```sql
\dt
```

Controllare utenti:

```sql
SELECT username, email, enabled FROM user_entity;
```

Controllare realm:

```sql
SELECT name, enabled FROM realm;
```

Uscire:

```sql
\q
```

Oppure diretto:

```bash
docker exec -it iso-audit-keycloak-db psql -U admin_audit -d keycloak
```

---

## 7) Accedere al DB ISO Audit

```bash
docker exec -it iso-audit-db psql -U iso_user -d iso_audit
```

---

## 8) Log e Debug

Keycloak:

```bash
docker logs -f iso-audit-keycloak
```

Backend:

```bash
docker logs -f iso-audit-backend
```

Stato container:

```bash
docker compose ps
```

---

## 9) Endpoint OIDC utili

Issuer:

- `http://localhost:9000/realms/iso-audit`

JWKS:

- `http://localhost:9000/realms/iso-audit/protocol/openid-connect/certs`

Token endpoint:

- `http://localhost:9000/realms/iso-audit/protocol/openid-connect/token`

---

## Note Importanti

- `admin_audit/admin123` → solo Admin Console
- `javid/Javid123!` → utente realm `iso-audit`
- Import funziona solo su DB Keycloak vuoto
- Evitare mount host su macOS
- Usare `docker cp` per import stabile
- DB ISO Audit e DB Keycloak sono separati (best practice)
