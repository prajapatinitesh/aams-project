import qrcode
import io, base64
from django.core import signing
from django.conf import settings
from accounts.models import SystemConfig

def generate_signed_token(session_id: int) -> str:
    """Returns a signed token string encoding session_id + timestamp."""
    return signing.dumps({"session_id": session_id}, salt="qr-attendance")

def verify_token(token: str, max_age: int) -> dict:
    """Raises signing.BadSignature or signing.SignatureExpired if invalid."""
    return signing.loads(token, salt="qr-attendance", max_age=max_age)

def token_to_qr_base64(token: str, attend_base_url: str) -> str:
    """Generates a QR code PNG as base64 string from the attendance URL."""
    url = f"{attend_base_url}/attend/{token}/"
    img = qrcode.make(url)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{encoded}"
