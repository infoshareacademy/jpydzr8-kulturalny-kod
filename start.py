class Start:
    def run(self):
        while True:
            self.print_available_actions()
            user_choice = input("Wybierz, co chcesz zrobić: ")
            result = self.action_handler(user_choice)
            if not result:
                break
            return False

    def print_available_actions(self):
        print("\nDostępne akcje:")
        print("1. Login")
        print("2. Rejestracja")
        print("3. Wyjście")

    def action_handler(self, user_choice):
        if user_choice.lower == "Login":
            print("\nPodaj dane logowania:")
            login = input("Login: ")
            password = input("Hasło: ")
            user = user_list.login(login, password)
            if user:
                user.run()
                return True
            else:
                print("Nieprawidłowy login lub hasło.")
                return True

        elif user_choice.lower == "Register":
            print("\nZarejestruj się:")
            login = input("Podaj login: ")
            password = input("Utwórz hasło: ")
            if user_list.register(login, password):
                print("Rejestracja powiodła się. Możesz się teraz zalogować.")
            else:
                print("Użytkownik o takim loginie już istnieje.")
            return True

        elif user_choice.lower == "Exit":
            print("Zamykanie programu")
            return False

        else:
            print("Nieznana akcja")
            return True