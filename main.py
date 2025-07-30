


if __name__ == "__main__":
    user_list = UserList()
    user_list.load("nazwa_pliku.txt")

    event_list = EventList()
    event_list.load("nazwa_pliku.txt")

    start = Start()

    objekt = start.run()

def start.run -> bool:
    """
    wywołuje listę dostępnych akcji
    prosi o wybór akcji
    wywołuje konkretną akcję
    jeśli akcja zwróci false to kończy się program
    """
    while True:
        print_dostępnych_akcji
        user_choice = input("Wybierz akcję: ")
        objekt = start.action_handler(user_choice)
        if not objekt:
            break
        return objekt

def start.action_handler -> bool:

    if user_choice == "login":
        print_co_aplikacja_oczekuje_od_tej_funkcji
        login = input("Podaj login:")
        password = input("Podaj hasło:")
        user = user_list.login(login, password)
        user.run()
        return True
    elif user_choice == "Wyjście":
        return False
    return False

def user.run -> bool:
    while True:
        print_dostępnych_akcji
        user_choice = input("Wybierz akcję: ")
        objekt = user.action_handler(user_choice)
        if not objekt:
            break
    return False

def user.action_handler -> bool:
    if user_choice == "Wyjście":
        return False