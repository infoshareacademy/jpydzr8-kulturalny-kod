from booking_class import Booking
from ticket_class import Ticket


class Event:
    def __init__(self, event_id: int, name: str, date: str, venue: str, description:str,
                 total_seats: int, available_seats: int, category: str, price: float):
        """
        Inicjalizuje obiekt wydarzenia z podstawowymi informacjami.
        """
        self.event_id = event_id
        self.name = name
        self.date = date
        self.venue = venue
        self.description = description
        self.total_seats = total_seats
        self.available_seats = available_seats
        self.category = category
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
            booking.ticket = Ticket.generate(booking)
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
            "category" : self.category,
            "price" : self.price,
            "bookings" : len(self.bookings)
        }

    def to_dict(self):
        """
        Zwraca dane wydarzenia jako słownik.
        """
        return self.get_details()

    @staticmethod
    def from_dict(data):
        """
        Tworzy obiekt Event z danych słownikowych.
        """
        event = Event(
            data["event_id"],
            data["name"],
            data["date"],
            data["venue"],
            data["total_seats"],
            data.get("available_seats", data["total_seats"]),
            data["category"],
            data["price"]
        )
        return event