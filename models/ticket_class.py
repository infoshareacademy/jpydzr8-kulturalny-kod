import os

class Ticket:
    def __init__(self, booking, event):
        """
        Inicjalizuje nowy obiekt Ticket na podstawie rezerwacji i wydarzenia.

        """
        self.booking = booking
        self.event = event
        self.file_path = f"tickets/ticket_{booking.id}.txt" # Sciezka do pliku z biletem
        self.generate_txt() # Generowanie pliku tekstowego z biletem

    @classmethod
    def generate(cls, booking, event):
        """
        Tworzy nowy obiekt Ticket.

        """
        return Ticket(booking, event)

    def generate_txt(self):
        """
        Generuje plik tekstowy z biletem na podstawie danych rezerwacji i wydarzenia.
        Plik jest zapisywany w folderze 'tickets'.
        """
        os.makedirs("tickets", exist_ok=True) # Tworzy folder 'tickets', jesli nie istnieje

        # Zawartosc biletu
        content = (
            "==============================================\n"
            "         BILET NA WYDARZENIE\n"
            "==============================================\n"
            f"Nazwa wydarzenia : {self.event.name}\n"
            f"Data             : {self.event.date}\n"
            f"Miejsce          : {self.event.venue}\n"
            f"Rezerwujący      : {self.booking.user_name}\n"
            f"Ilość miejsc     : {self.booking.seats}\n"
            f"Data rezerwacji  : {self.booking.date}\n"
            "==============================================\n"
        )

        # Zapis zawartosci do pliku
        with open(self.file_path, "w", encoding="utf-8") as f:
            f.write(content)