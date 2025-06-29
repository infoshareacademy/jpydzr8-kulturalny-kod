import json
from datetime import datetime
import uuid
from models.ticket_class import Ticket


class Booking:
    def __init__(self, event_id: int, user_name: str, seats: int):
        """
        Inicjalizuje nową rezerwację.

        """
        self.id = str(uuid.uuid4()) # Unikalne ID rezerwacji
        self.event_id = event_id
        self.user_name = user_name
        self.seats = seats
        self.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S") # Data utworzenia rezerwacji
        self.ticket = None # Obiekt Ticket przypisany do rezerwacji (może być ustawiony później)


    def to_dict(self):
        """
        Zwraca reprezentację rezerwacji jako słownik.

        """
        return {
            "id": self.id,
            "event_id": self.event_id,
            "user_name": self.user_name,
            "seats": self.seats,
            "date": self.date,
            "ticket_path": self.ticket.file_path if self.ticket else None
        }

    @classmethod
    def save_to_file(cls, booking, filename="bookings.json"):
        """
        Zapisuje rezerwację do pliku JSON. Jeśli plik nie istnieje, tworzy nowy.

        """
        try:
            with open(filename, "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            data = [] # Jeśli plik nie istnieje, tworzymy pustą listę

        data.append(booking.to_dict())

        with open(filename, "w") as f:
            json.dump(data, f, indent=4) # Zapisuje z wcięciami dla czytelności