import json
from models.booking_class import Booking
from models.ticket_class import Ticket


class Event:
    def __init__(self, event_id: int, name: str, date: str, venue: str,
                 total_seats: int, available_seats: int, price: float):
        """
        Inicjalizuje obiekt wydarzenia z podstawowymi informacjami.
        """
        self.event_id = event_id
        self.name = name
        self.date = date
        self.venue = venue
        self.total_seats = total_seats
        self.available_seats = available_seats
        self.price = price
        self.bookings = []


    def has_available_seats(self):
        """
        Sprawdza czy są dostępne miejsca na wydarzenie.
        """
        return self.available_seats > 0

    def add_booking(self,booking: Booking) -> bool:
        """
        Dodaje rezerwację do wydarzenia, jeśli są wystarczające wolne miejsca.
        Tworzy również bilet dla rezerwacji.
        Zwraca True jeśli rezerwacja została dodana, w przeciwnym razie False.
        """
        if booking.seats <= self.available_seats:
            self.available_seats -= booking.seats
            self.bookings.append(booking)
            booking.ticket = Ticket.generate(booking, self)
            return True
        return False

    def cancel_booking(self, booking_id: int) -> bool:
        """
        Anuluje rezerwację na podstawie identyfikatora rezerwacji.
        Zwiększa liczbę dostępnych miejsc i usuwa rezerwację z listy.
        Zwraca True jeśli anulowano, w przeciwnym razie False.
        """
        for booking in self.bookings:
            if booking.id == booking_id:
                self.available_seats += booking.seats
                self.bookings.remove(booking)
                return True
        return False

    def get_details(self) -> dict:
        """
        Zwraca szczegóły wydarzenia jako słownik.
        """
        return {
            "event_id" : self.event_id,
            "name" : self.name,
            "date" : self.date,
            "venue" : self.venue,
            "total_seats" : self.total_seats,
            "available_seats" : self.available_seats,
            "price" : self.price,
            "bookings" : len(self.bookings)
        }

    def to_dict(self):
        """
        Zwraca dane wydarzenia jako słownik.
        """
        return self.get_details()

    @classmethod
    def from_dict(cls, data):
        """
        Tworzy obiekt Event z danych słownikowych.
        """
        event = Event(
            data["event_id"],
            data["name"],
            data["date"],
            data["venue"],
            data["total_seats"],
            data.get("available_seats",
            data["total_seats"]),
            data["price"]
        )
        event.available_seats = data.get("available_seats", event.total_seats)
        return event

class EventList:
    def __init__(self):
        self.events = []

    def load_from_file(self, filename):
        with open(filename, "r") as f:
            data = json.load(f)
            for event_data in data:
                event = Event.from_dict(self._convert_keys(event_data))
                self.events.append(event)

    def save_to_file(self, filename):
        data = [event.to_dict() for event in self.events]
        with open(filename, "w") as f:
            json.dump(data, f, indent=4)

    def _convert_keys(self, data: dict) -> dict:
        return {
            "event_id": data.get("event_id"),
            "name": data.get("name"),
            "date": data.get("date"),
            "venue": data.get("venue"),
            "total_seats": data.get("total_seats"),
            "available_seats": data.get("available_seats"),
            "price": data.get("price")
        }