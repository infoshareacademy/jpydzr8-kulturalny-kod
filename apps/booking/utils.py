import io
import qrcode
from django.core.files.base import ContentFile

def generate_ticket_number(prefix='TKT'):
    from uuid import uuid4
    return f"{prefix}-{uuid4().hex[:10].upper()}"

def make_qr_code(data: str) -> ContentFile:
    img = qrcode.make(data)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return ContentFile(buf.getvalue(), name='qr.png')
