import qrcode
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from django.core.files.base import ContentFile

def generate_ticket_pdf(user, event, receipt_no):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)

    p.setFont("Helvetica-Bold", 18)
    p.drawString(100, 770, f"TICKET - {event.title}")
    p.setFont("Helvetica", 12)

    p.drawString(100, 730, f"Name: {user.get_full_name() or user.username}")
    p.drawString(100, 710, f"Phone: {user.username}")
    p.drawString(100, 690, f"Event Date: {event.date}")
    p.drawString(100, 670, f"Event Location: {event.location}")
    p.drawString(100, 650, f"Receipt No: {receipt_no}")

    # Generate QR code
    qr_data = f"{event.id}-{receipt_no}"
    qr = qrcode.make(qr_data)
    qr_io = BytesIO()
    qr.save(qr_io)
    p.drawInlineImage(qr_io, 400, 650, 120, 120)

    p.showPage()
    p.save()

    buffer.seek(0)
    return buffer.getvalue()
