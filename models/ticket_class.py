import os
import qrcode
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

class Ticket:
    def __init__(self, booking, event):
        self.booking = booking
        self.event = event
        self.file_path = f"tickets/ticket_{booking.id}.pdf"
        self.qr_path = f"tickets/qr_{booking.id}.png"
        self.generate_pdf()

    @classmethod
    def generate(cls, booking, event):
        return Ticket(booking, event)

    def generate_qr_code(self):
        os.makedirs("tickets", exist_ok=True)
        qr_data = (
            f"Rezerwacja ID: {self.booking.id}\n"
            f"Użytkownik: {self.booking.user_name}\n"
            f"Wydarzenie: {self.event.name}"
        )
        qr = qrcode.make(qr_data)
        qr.save(self.qr_path)

    def generate_pdf(self):
        self.generate_qr_code()

        c = canvas.Canvas(self.file_path, pagesize=A4)
        width, height = A4

        # Nagłówek
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(width / 2, height - 50, "BILET NA WYDARZENIE")
        c.setFont("Helvetica", 12)

        # Pozycjonowanie treści
        text_x = 80
        text_y = height - 100
        line_height = 20

        # Dane tekstowe
        data = [
            f"Nazwa wydarzenia : {self.event.name}",
            f"Data             : {self.event.date}",
            f"Miejsce          : {self.event.venue}",
            f"Rezerwujacy      : {self.booking.user_name}",
            f"Ilosc miejsc     : {self.booking.seats}",
            f"Data rezerwacji  : {self.booking.date}",
        ]

        for line in data:
            c.drawString(text_x, text_y, line)
            text_y -= line_height

        # Kod QR po prawej stronie danych
        qr_img = ImageReader(self.qr_path)
        qr_size = 120
        qr_x = width - text_x - qr_size  # margines z prawej
        qr_y = height - 100 - qr_size  # dokładnie górna krawędź QR == tekst_y początkowy
        c.drawImage(qr_img, qr_x, qr_y, width=qr_size, height=qr_size)

        # Stopka
        c.setFont("Helvetica-Oblique", 10)
        c.drawString(text_x, 80, "Dziekujemy za rezerwacje!")

        c.save()

        os.remove(self.qr_path) # usuń tymczasowy plik QR
