# Project

## Requirements
- Docker
- Docker Compose

## Quick start (dev)
1. Copy env template:
   - cp .env.example .env
2. Start:
   - docker compose up --build

## Notes
- Do not commit `.env`

## example di utility of loger 
```python
from iso_27001_audit.logger.audit import AuditLogger

audit_log = AuditLogger(__name__)
audit_log.audit_event(action="USER_LOGIN", subject="user_id:123", details={"ip": "1.2.3.4"})
```
