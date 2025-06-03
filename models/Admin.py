from uuid import uuid4
from datetime import datetime
from UserManager import UserManager
from EventManager import EventManager


class Admin:
    list_of_actions = {
        "wyświetl dostępne możliwe akcje": "print_of_actions",
        "utwórz admina": "create_admin",
        "usuń admina": "delete_admin",
        "utwórz wydarzenie": "create_event",
        "usuń wydarzenie": "delete_event",
        "dodaj użytkownika": "add_user",
        "usuń użytkownika": "delete_user",
        "anuluj rezerwację": "cancel_booking",
        "dodaj rezerwację": "add_booking",
        # "edytuj rezerwację": "edit_booking",
        # "edytuj użytkownika": "edit_user",
        # "edytuj wydarzenie": "edit_event",
        # "wyświetl listę wydarzeń": "print_of_events",
        # "wyświetl listę użytkowników": "print_of_users",
        # "wyświetl listę rezerwacji": "print_of_bookings",
        # "wyświetl informacje o użytkowniku": "print_user_info",
        # "wyświetl informacje o wydarzeniu": "print_event_info",
        # "wyświetl informacje o rezerwacji": "print_booking_info",
        "wyjście": "exit",
    }

    def __init__(self, login: str, password: str):
        self.__id = str(uuid4())
        self.__created_at = datetime.now()
        self.__login = login
        self.__password = password
        self.__is_admin = True

    @staticmethod
    def __get_dict_from_string(string: str) -> dict:
        """
        Create a dictionary from a string like
        key1: value1, key2: value2
        """
        list_ = string.replace(" ", "").split(",")
        attr_dict = {}
        for attribute in list_:
            attribute = attribute.split(":")
            attr_dict[attribute[0]] = attribute[1]
        return attr_dict

    @property
    def id(self) -> str:
        return self.__id
    
    @staticmethod
    def exit():
        return False

    def print_of_actions(self) -> None:
        """
        prints all available actions
        """
        for i, key in enumerate(self.list_of_actions.keys()):
            print(f"{i}. {key.capitalize()}")

    def action(self) -> None:
        """
        asks the user to select an action and executes it
        goes forever until action result is not False
        """
        action_name = input("Enter action: ")
        action_name = action_name.lower()
        if action_name in self.list_of_actions.keys():
            action = self.list_of_actions[action_name]
            action_result = getattr(self, action)()
            print(
                f"Action {action_name} was successful with result {action_result}"
                if action_result
                else f"Action {action_name} was failed"
            )
            if action_result:
                self.action()
        else:
            print("Invalid action")
            self.action()

    @classmethod
    def create_admin(cls, user_manager: UserManager) -> str:
        """
        creates a new admin and adds it to list of users
        """
        login = input("Enter login: ")
        password = input("Enter password: ")
        admin = cls(login, password)
        user_manager.add_user(admin)
        print(f"New admin created with ID: {admin.id}")
        return admin.id

    def delete_admin(self, user_manager: UserManager) -> str:
        """
        deletes an admin from list of users
        """
        id = input("Enter id of admin to delete: ")
        result = user_manager.delete_user(id, is_admin=self.__is_admin)
        if result:
            print(f"Admin with id {id} was deleted")
        else:
            print(f"There is no admin with id {id}")
        return True

    def create_event(self, event_manager: EventManager) -> str:
        """
        creates event and adds it to list of events
        """
        print("Potrzebne dane:")
        print("Name:XXX,Date:yyyy-mm-dd,Capacity:XXX") # zastanowić się, czy podawanie atrybutuów nie powinno być w ramach metody add_event w event_manager
        event_data = input("Enter event data: ")
        event_attr_dict = self.__get_dict_from_string(event_data)
        id = event_manager.add_event(is_admin=self.__is_admin, **event_attr_dict)
        return id

    def delete_event(self, event_manager: EventManager) -> str:
        id = input("Enter id of event to delete: ")
        result = event_manager.delete_event(id, is_admin=self.__is_admin)
        return True

    def edit_event(self, event_manager: EventManager) -> str:
        print("Potrzebne dane:")

    def add_user(self, user_manager: UserManager) -> str:
        print("Potrzebne dane:")
        print("login:XXX,password:XXX,date_of_birth:yyyy-mm-dd") # zastanowić się, czy podawanie atrybutuów nie powinno być w ramach metody add_user w user_manager
        user_data = input("Enter event data: ")
        user_attr_dict = self.__get_dict_from_string(user_data)
        id = user_manager.add_user(is_admin=self.__is_admin, **user_attr_dict)
        return id

    def delete_user(self, user_manager: UserManager) -> str:
        id = input("Enter id of user to delete: ")
        result = user_manager.delete_user(id, is_admin=self.__is_admin)
        return id

    def edit_user(self, user_manager: UserManager) -> str:
        pass

    def cancel_booking(
            self,
            event_manager: EventManager,
            user_manager: UserManager,
    ) -> str:
        user_id = input("Enter id of user: ")
        event_id = input("Enter id of event: ")
        user = user_manager.get_user(user_id, is_admin=self.__is_admin)
        if user:
            result = event_manager.cancel_booking(user, event_id, is_admin=self.__is_admin)
        return True

    def edit_booking(
            self,
            event_manager: EventManager,
            user_manager: UserManager,
    ) -> str:
        pass

    def add_booking(
            self,
            event_manager: EventManager,
            user_manager: UserManager,
    ) -> str:
        user_id = input("Enter id of user: ")
        event_id = input("Enter id of event: ")
        user = user_manager.get_user(user_id, is_admin=self.__is_admin)
        if user:
            booking_id = event_manager.add_booking(user, event_id, is_admin=self.__is_admin)
        return booking_id


if __name__ == "__main__":
    admin = Admin("admin", "admin")
    admin.print_of_actions()
