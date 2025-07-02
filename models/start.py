# start.py

import os
import sys
import json
from uuid import uuid4
from datetime import datetime

from user import UsersManagement, User, Admin, ValidationError
from event_class import EventList


DATA_DIR = "../data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")
EVENTS_FILE = os.path.join(DATA_DIR, "events.json")


def load_users(users_file):
    um = UsersManagement()
    if os.path.exists(users_file):
        try:
            um.load_from_json_file(users_file)
        except Exception as e:
            print(f"Błąd podczas ładowania użytkowników: {e}")
    else:
        print(f"Plik {users_file} nie istnieje. Tworzę pustą bazę użytkowników.")
    return um

def load_events(events_file):
    el = EventList()
    if os.path.exists(events_file):
        try:
            el.load_from_file(events_file)
        except Exception as e:
            print(f"Błąd podczas ładowania wydarzeń: {e}")
    else:
        print(f"Plik {events_file} nie istnieje. Tworzę pustą bazę wydarzeń.")
    return el

def main_menu():
    print("\n=== SYSTEM REZERWACJI WYDARZEŃ ===")
    print("1. Zaloguj się jako użytkownik")
    print("2. Zaloguj się jako administrator")
    print("3. Zarejestruj się jako nowy użytkownik")
    print("4. Wyjdź z programu")
    return input("Wybierz opcję: ").strip()

def admin_login(users_management):
    print("\n--- Logowanie administratora ---")
    login = input("Login: ").strip()
    password = input("Hasło: ").strip()
    user = users_management.login(login, password)
    if user and getattr(user, "is_admin", False):
        print("Zalogowano jako administrator.")
        return user
    print("Błędny login lub brak uprawnień administratora.")
    return None

def user_login(users_management):
    print("\n--- Logowanie użytkownika ---")
    login = input("Login: ").strip()
    password = input("Hasło: ").strip()
    user = users_management.login(login, password)
    if user and not getattr(user, "is_admin", False):
        print(f"Zalogowano jako użytkownik: {user.login}")
        return user
    print("Błędny login lub nie jesteś użytkownikiem.")
    return None

def register_user(users_management):
    print("\n--- Rejestracja nowego użytkownika ---")
    while True:
        login = input("Podaj login (min. 5 znaków): ").strip()
        if login in users_management.users:
            print("Taki login już istnieje. Wybierz inny.")
            continue
        password = input("Podaj hasło (min. 8 znaków): ").strip()
        email = input("Podaj email: ").strip()
        data_urodzenia = input("Podaj datę urodzenia (YYYY-MM-DD): ").strip()
        try:
            birthdate = datetime.strptime(data_urodzenia, "%Y-%m-%d").date()
            user_id = str(uuid4())
            user = User(login, password, email, birthdate, user_id)
            users_management.users[login] = user
            print("Rejestracja zakończona sukcesem! Możesz się teraz zalogować.")
            return True
        except ValidationError as e:
            print(f"Błąd walidacji: {e}")
        except Exception as e:
            print(f"Błąd: {e}")

def create_first_admin(users_management):
    print("\n--- Tworzenie pierwszego administratora ---")
    while True:
        login = input("Podaj login admina: ").strip()
        password = input("Podaj hasło admina: ").strip()
        email = input("Podaj email admina: ").strip()
        data_urodzenia = input("Podaj datę urodzenia (YYYY-MM-DD): ").strip()
        try:
            birthdate = datetime.strptime(data_urodzenia, "%Y-%m-%d").date()
            admin = Admin(login, password, email, birthdate, str(login) + "_admin")
            users_management.users[login] = admin
            print("Admin utworzony!")
            break
        except ValidationError as e:
            print(f"Błąd walidacji: {e}")
        except Exception as e:
            print(f"Błąd: {e}")

def save_all(users_management, event_list):
    # Zapisuje użytkowników
    users_data = {"users": []}
    for user in users_management.users.values():
        if hasattr(user, "data_urodzenia") and hasattr(user, "id"):
            users_data["users"].append({
                "login": user.login,
                "password": user.password,
                "email": user.email,
                "data_urodzenia": str(user.data_urodzenia),
                "id": user.id,
                "is_admin": getattr(user, "is_admin", False)
            })

    os.makedirs(DATA_DIR, exist_ok=True)
    with open(USERS_FILE, "w") as f:
        json.dump(users_data, f, indent=4)
    # Zapisz wydarzenia
    event_list.save_to_file(EVENTS_FILE)

def run():
    users_management = load_users(USERS_FILE)
    event_list = load_events(EVENTS_FILE)

    # Jeśli nie ma żadnego admina, wymusza utworzenie
    if not any(getattr(u, "is_admin", False) for u in users_management.users.values()):
        print("\nBrak administratora w systemie.")
        create_first_admin(users_management)
        save_all(users_management, event_list)

    while True:
        choice = main_menu()
        if choice == "1":
            user = user_login(users_management)
            if user:
                user.run(event_list)
                save_all(users_management, event_list)
        elif choice == "2":
            admin = admin_login(users_management)
            if admin:
                from admin import Admin as AdminMenu
                admin_menu = AdminMenu(admin.login, admin.password)
                admin_menu.run(user_management=users_management, event_list=event_list)
                save_all(users_management, event_list)
        elif choice == "3":
            if register_user(users_management):
                save_all(users_management, event_list)
        elif choice == "4":
            print("Do widzenia!")
            save_all(users_management, event_list)
            sys.exit(0)
        else:
            print("Nieznana opcja. Spróbuj ponownie.")

if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("\nDo widzenia!")
        sys.exit(0)
