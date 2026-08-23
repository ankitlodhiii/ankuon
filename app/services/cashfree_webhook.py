import hmac
import hashlib
import base64
from django.conf import settings


def verify_cashfree_signature(raw_body: str, timestamp: str, signature: str) -> bool:
    if not timestamp or not signature or raw_body is None:
        return False

    secret = getattr(settings, 'CASHFREE_SECRET_KEY', '') or ''
    if not secret:
        return settings.DEBUG

    signed_payload = f"{timestamp}{raw_body}"
    dig = hmac.new(
        secret.encode('utf-8'),
        signed_payload.encode('utf-8'),
        hashlib.sha256,
    ).digest()
    computed = base64.b64encode(dig).decode('utf-8')
    return hmac.compare_digest(computed, signature)
