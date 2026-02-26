from .base import BaseLogger


class AuditLogger(BaseLogger):
    """
    Audit logger: use it for audit trail events (ISO-27001).
    """

    def __init__(self, module_name):
        super().__init__(module_name)

    def audit_event(self, action, subject, details=None):
        payload = {
            "action": action,
            "subject": subject,
            "details": details or {},
        }
        self.get().info("AUDIT %s", payload)