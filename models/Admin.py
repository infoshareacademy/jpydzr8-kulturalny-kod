from uuid import uuid4
from datetime import datetime
from user import UsersManagement
from event import EventList


def cast_value(value: str) -> int | float | str:
    try:
        float_value = float(value)
        int_value = int(value)
        if int_value == float_value:
            return int_value
        else:
            return float_value
    except ValueError:
        return value
    except Exception as e:
        print(f"Unexpected error {e}")
        return False
    

class Admin:
    list_of_actions = {
        "wyświetl dostępne możliwe akcje": "print_of_actions",
        "utwórz admina": "create_admin",
        "usuń admina": "delete_admin",
        "utwórz wydarzenie": "create_event",
        "usuń wydarzenie": "delete_event",
        "dodaj użytkownika": "create_user",
        "usuń użytkownika": "delete_user",
        "dodaj rezerwację": "add_booking",
        "anuluj rezerwację": "cancel_booking",
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
            attr_dict[attribute[0]] = cast_value(attribute[1])
        return attr_dict

    @property
    def id(self) -> str:
        return self.__id
    
    @staticmethod
    def exit(**kwargs):
        print("Wylogowano admina")
        return False

    def print_of_actions(self) -> None:
        """
        prints all available actions
        """
        for i, key in enumerate(self.list_of_actions.keys()):
            print(f"{i}. {key.capitalize()}")

    def run(
        self, 
        user_management: UsersManagement, 
        event_list: EventList,
        **kwargs
    ) -> None:
        """
        asks the user to select an action and executes it
        goes forever until action result is not False
        """
        self.print_of_actions()
        action_name = input("Enter action: ")
        action_name = action_name.lower()
        if action_name in self.list_of_actions.keys():
            action = self.list_of_actions[action_name]
            action_result = getattr(self, action)(
                user_management=user_management, 
                event_list=event_list,
            )
            if action_result:
                print(f"Action {action_name} was successful with result {action_result}")
                self.action()
        else:
            print("Invalid action")
            self.action()

    @classmethod
    def create_admin(cls, user_management: UsersManagement, **kwargs) -> str:
        """
        creates a new admin and adds it to list of users
        """
        login = input("Enter login: ")
        password = input("Enter password: ")
        admin = cls(login, password)
        user_management.users[login] = admin
        print(f"New admin created with ID: {admin.id}")
        return admin.id

    def delete_admin(self, user_management: UsersManagement, **kwargs) -> str:
        """
        deletes an admin from list of users
        """
        id = input("Enter id of admin to delete: ")
        result = user_management.users.pop(id, None)
        if result:
            print(f"Admin with id {id} was deleted")
        else:
            print(f"There is no admin with id {id}")
        return True

    def create_event(self, event_list: EventList, **kwargs) -> str:
        """
        creates event and adds it to list of events
        """
        print("Potrzebne dane:")
        id = str(uuid4())
        print("name:XXX,date:yyyy-mm-dd,venue:XXX,total_seats:XXX,available_seats:XXX,price:float")
        event_data = input("Enter event data: ")
        event_attr_dict = self.__get_dict_from_string(event_data)
        event_attr_dict["id"] = id
        id = event_list.add_event(is_admin=self.__is_admin, **event_attr_dict)
        return id

    def delete_event(self, event_list: EventList, **kwargs) -> str:
        id = input("Enter id of event to delete: ")
        result = event_list.delete_event(id, is_admin=self.__is_admin)
        return True

    def edit_event(self, event_list: EventList, **kwargs) -> str:
        print("Potrzebne dane:")

    def create_user(self, user_management: UsersManagement, **kwargs) -> str:
        print("Potrzebne dane:")
        id = str(uuid4())
        print("login:XXX,password:XXX,email:XXX,data_urodzenia:yyyy-mm-dd")
        user_data = input("Enter event data: ")
        user_attr_dict = self.__get_dict_from_string(user_data)
        user_attr_dict["id"] = id
        result = user_management.create_user(current_user=self, **user_attr_dict)
        return result

    def delete_user(self, user_management: UsersManagement, **kwargs) -> str:
        login = input("Enter login of user to delete: ")
        result = user_management.delete_user(current_user=self, user_login=login)
        return result

    def edit_user(self, user_management: UsersManagement, **kwargs) -> str:
        pass

    def cancel_booking(
            self,
            event_list: EventList,
            user_management: UsersManagement,
            **kwargs
    ) -> str:
        user_login = input("Enter login of user: ")
        event_id = input("Enter id of event: ")
        user = user_management.users.get(user_login)
        if user:
            result = event_list.cancel_booking(user, event_id)
        return True

    def edit_booking(
            self,
            event_list: EventList,
            user_management: UsersManagement,
            **kwargs
    ) -> str:
        pass

    def add_booking(
            self,
            event_list: EventList,
            user_management: UsersManagement,
            **kwargs
    ) -> str:
        user_login = input("Enter login of user: ")
        event_id = input("Enter id of event: ")
        seats = int(input("Enter how many tickets do you wanna book: "))
        user = user_management.users.get(user_login)
        event = event_list.get_event(event_id)
        if user:
            result = user.add_booking(event=event, seats=seats)
        return True


if __name__ == "__main__":
    admin = Admin("admin", "admin")
    user_management = UsersManagement()
    event_list = EventList()
    
    admin.run(
        user_management=user_management,
        event_list=event_list
    )
