from models.booking_class import Booking
from datetime import datetime, date
import json
import os


def calculate_age(birthdate):
    today = date.today()
    return today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))

class ValidationError(Exception):
    pass

class User:
    def __init__(self, login, password, email, data_urodzenia, id):
        if len(login) < 5:
            raise ValidationError("Login musi mieć co najmniej 5 znaków.")
        if len(password) < 8:
            raise ValidationError("Hasło musi mieć co najmniej 8 znaków.")
        if "@" not in email or "." not in email:
            raise ValidationError("Niepoprawny adres e-mail.")
        if calculate_age(data_urodzenia) < 18:
            raise ValidationError("Użytkownik musi mieć co najmniej 18 lat.")

        self.login = login
        self.is_admin = False
        self.password = password
        self.email = email
        self.data_urodzenia = data_urodzenia
        self.created_at = datetime.now()
        self.changed_at = None
        self.booking_list = []
        self.id = id

    def run(self, event_list):
        while True:
            print(f"\nWitaj, {self.login}. Co chcesz zrobić?")
            print("1. Zobacz dostępne wydarzenia")
            print("2. Zarezerwuj miejsce na wydarzenie")
            print("3. Pokaż moje rezerwacje")
            print("4. Anuluj rezerwację")
            print("5. Wyloguj")

            choice = input("Wybierz opcję: ").strip()

            if choice == "1":
                print("\nDostępne wydarzenia:")
                for event in event_list.events:
                    details = event.get_details()
                    print(f"ID: {details['event_id']}, Nazwa: {details['name']}, "
                          f"Data: {details['date']}, Miejsca dostępne: {details['available_seats']}, "
                          f"Cena: {details['price']} PLN")

            elif choice == "2":
                try:
                    event_id = int(input("Podaj ID wydarzenia: "))
                    seats = int(input("Podaj liczbę miejsc: "))
                    event = next((e for e in event_list.events if e.event_id == event_id), None)
                    if event:
                        self.add_booking(event, seats)
                    else:
                        print("Nie znaleziono wydarzenia o podanym ID.")
                except ValueError:
                    print("Błędne dane. Spróbuj ponownie.")

            elif choice == "3":
                if not self.booking_list:
                    print("Brak rezerwacji.")
                else:
                    print("\nTwoje rezerwacje:")
                    for b in self.booking_list:
                        print(f"ID: {b.id}, Wydarzenie: {b.event_id}, Miejsca: {b.seats}, Data: {b.date}")

            elif choice == "4":
                booking_id = input("Podaj ID rezerwacji do anulowania: ").strip()
                success = self.cancel_booking(booking_id)
                if not success:
                    print("Nie udało się anulować rezerwacji.")

            elif choice == "5":
                print("Wylogowano.")
                break

            else:
                print("Nieznana opcja. Spróbuj ponownie.")

    def add_booking(self, event, seats=1):
        if any(b.event_id == event.event_id for b in self.booking_list):
            print("Rezerwacja na to wydarzenie już istnieje.")
            return False

        if not event.has_available_seats() or seats > event.available_seats:
            print("Brak dostępnych miejsc.")
            return False

        booking = Booking(event_id=event.event_id, user_name=self.login, seats=seats)
        if event.add_booking(booking):
            self.booking_list.append(booking)
            Booking.save_to_file(booking)
            print(f"Zarezerwowano {seats} miejsc na wydarzenie: {event.name}")
            return True
        return False

    def cancel_booking(self, booking_id):
        for booking in self.booking_list:
            if booking.id == booking_id:
                if booking.event_id and booking.event_id == booking.event_id:
                    self.booking_list.remove(booking)
                    print("Rezerwacja anulowana.")
                    return True
        print("Nie znaleziono rezerwacji.")
        return False

    @property
    def age(self):
        return calculate_age(self.data_urodzenia)

class Admin(User):
    def __init__(self, user_login, user_password, user_email_address, birthdate, user_id):
        super().__init__(user_login, user_password, user_email_address, birthdate, user_id)
        self.is_admin = True

class UsersManagement:
    def __init__(self):
        self.users = {}

    def print_options(self):
        print("Dostępne metody: create_user, edit_user, delete_user, login")

    def login(self, login, password):
        user = self.users.get(login)
        if not user:
            print("Nie znaleziono użytkownika o takim loginie.")
            return None
        if user.password != password:
            print("Błędne hasło.")
            return None
        return user

    def create_user(self, login, password, email, data_urodzenia, id, current_user):
        if not current_user.is_admin:
            return False
        user = User(login, password, email, data_urodzenia, id)
        self.users[login] = user
        return True

    def edit_user(self, current_user, user_login, user_details_for_change):
        if not current_user.is_admin:
            print("Brak uprawnień administracyjnych.")
            return False

        user = self.users.get(user_login)
        if not user or user.is_admin:
            print("Nie znaleziono użytkownika lub próba edycji admina.")
            return False

        for key, value in user_details_for_change.items():
            setattr(user, key, value)

        user.changed_at = datetime.now()
        return True

    def delete_user(self, current_user, user_login):
        if not current_user.is_admin:
            print("Brak uprawnień administracyjnych.")
            return False

        user = self.users.get(user_login)
        if not user or user.is_admin:
            print("Nie znaleziono użytkownika lub próba usunięcia admina.")
            return False

        del self.users[user_login]
        return True

    def load_from_json_file(self, filepath, verbose=True):
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Plik nie istnieje: {filepath}")

        with open(filepath) as f:
            data = json.load(f)

        loaded_count = 0
        skipped_count = 0

        for u in data.get("users", []):
            try:
                birthdate = datetime.strptime(u["data_urodzenia"], "%Y-%m-%d").date()
                user = User(
                    login=u["login"],
                    password=u["password"],
                    email=u["email"],
                    data_urodzenia=birthdate,
                    id=u["id"]
                )
                self.users[user.login] = user
                loaded_count += 1
            except ValidationError as e:
                skipped_count += 1
                if verbose:
                    print(f"Walidacja nie powiodła się dla {u.get('login', '?')}: {e}")
            except Exception as e:
                skipped_count += 1
                if verbose:
                    print(f"Inny błąd dla {u.get('login', '?')}: {e}")

        print(f"Załadowano {loaded_count} użytkowników.", end=' ')
        if skipped_count:
            print(f"Pominięto {skipped_count} z powodu błędów.")
        else:
            print("Wszyscy użytkownicy zostali poprawnie załadowani.")