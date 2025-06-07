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
        self.password = password
        self.email= email
        self.created_at = datetime.now()
        self.changed_at = None
        self.booking_list = []
        self.age = calculate_age(data_urodzenia)
        self.id = id

    def add_booking(self, event_id):
        if event_id in self.booking_list:
            print("Rezerwacja już istnieje")
            return False
        self.booking_list.append(event_id)
        print("Aktualne rezerwacje:", self.booking_list)
        return True

    def cancel_booking(self, user_id, event_id):
        if self.id != user_id or event_id not in self.booking_list:
            return False
        self.booking_list.remove(event_id)
        print("Rezerwacja anulowana.")
        return True

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
        if user and user.user_password == password:
            return user.user_id
        return None

    def __is_admin(self, login, password):
        user = self.login(login, password)
        return isinstance(user, Admin)

    def create_user(self, new_user, admin_login, admin_password):
        if not self.__is_admin(admin_login, admin_password):
            return False
        if new_user.user_login in self.users:
            return False
        self.users[new_user.user_login] = new_user
        return True

    def edit_user(self, admin_login, admin_password, user_id, user_details_for_change):
        if not self.__is_admin(admin_login, admin_password):
            return False
        user = self.users.get(user_id)
        if not user or isinstance(user, Admin):
            return False
        for key, value in user_details_for_change.items():
            setattr(user, key, value)
        user.user_changed_at = datetime.now()
        return True

    def delete_user(self, admin_login, admin_password, user_login):
        if not self.__is_admin(admin_login, admin_password):
            return False
        user = self.users.get(user_login)
        if not user or isinstance(user, Admin):
            return False
        del self.users[user_login]
        return True

    def load_from_json_file(self, filepath):
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Plik nie istnieje: {filepath}")

        with open(filepath) as f:
            data = json.load(f)

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
                print(f"Dodano użytkownika: {user.login}")
            except ValidationError as e:
                print(f"Walidacja nie powiodła się dla {u['login']}: {e}")
            except Exception as e:
                print(f"Inny błąd dla {u['login']}: {e}")