def print_available_actions():
    print("\nDostępne akcje:")
    print("1. Login")
    print("2. Rejestracja")
    print("3. Wyjście")

def action_handler(user_choice, user_list):
    user_choice = user_choice.lower()

    if user_choice in ("1", "login"):
        print("\nPodaj dane logowania:")
        login = input("Login: ")
        password = input("Hasło: ")
        user = user_list.login(login, password)
        if user:
            user.run()
        else:
            print("Nieprawidłowy login lub hasło.")
        return True

    elif user_choice in ("2", "rejestracja", "register"):
        print("\nZarejestruj się:")
        login = input("Podaj login: ")
        password = input("Utwórz hasło: ")
        if user_list.register(login, password):
            print("Rejestracja powiodła się. Możesz się teraz zalogować.")
        else:
            print("Użytkownik o takim loginie już istnieje.")
        return True

    elif user_choice in ("3", "exit", "wyjście"):
        print("Zamykanie programu.")
        return False

    else:
        print("Nieznana akcja.")
        return True

def main_menu(user_list):
    while True:
        print_available_actions()
        user_choice = input("Wybierz, co chcesz zrobić: ")
        if not action_handler(user_choice, user_list):
            break