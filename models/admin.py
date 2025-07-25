from uuid import uuid4
from datetime import datetime

from .event_class import Event, EventList
from .user import UsersManagement


def cast_value(value: str) -> int | float | str:
    try:
        try:
            date_value = datetime.strptime(value, "%Y-%m-%d")
            return date_value
        except ValueError:
            float_value = float(value)
            int_value = int(float_value)
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
    def __get_dict_from_string(required_attributes: str, string: str) -> dict:
        """
        Create a dictionary from a string like
        key1: value1, key2: value2
        """
        attrs_list = required_attributes.split(",")
        list_ = string.strip(" ").split(",")
        attr_dict = {}
        for attribute, value in zip(attrs_list, list_):
            attr_iter = attribute.split(":")[0]
            attr_dict[attr_iter] = cast_value(value)
        return attr_dict

    def __get_action_from_input(self, action_name: str) -> str | bool:
        try:
            number = int(action_name)
            if number < 0 or number > len(self.list_of_actions):
                action_value = False
            else:
                action_value = list(self.list_of_actions.values())[number]
        except ValueError:
            action_value = self.list_of_actions.get(action_name, False)

        return action_value

    @property
    def is_admin(self) -> bool:
        return self.__is_admin
    
    @property
    def password(self) -> bool:
        return self.__password
    
    @property
    def login(self) -> bool:
        return self.__login

    @property
    def id(self) -> str:
        return self.__id

    @staticmethod
    def exit(**kwargs):
        print("Wylogowano admina")
        return False

    def print_of_actions(self, **kwargs) -> bool:
        """
        prints all available actions
        """
        for i, key in enumerate(self.list_of_actions.keys()):
            print(f"{i}. {key.capitalize()}")

        return True

    def run(
        self, user_management: UsersManagement, event_list: EventList, **kwargs
    ) -> None:
        """
        asks the user to select an action and executes it
        goes forever until action result is not False
        """
        self.print_of_actions()
        action_name = input("Enter action: ")
        action_name = action_name.lower()
        action = self.__get_action_from_input(action_name)
        if action:
            try:
                action_result = getattr(self, action)(
                    user_management=user_management,
                    event_list=event_list,
                )

                if action_result:
                    print(
                        f"Action {action} was successful with result {action_result}"
                    )
                    self.run(user_management=user_management, event_list=event_list)

            except AttributeError:
                print(f"Wrong attributes passed to function {action_name}")
                self.run(user_management=user_management, event_list=event_list)

        else:
            print("Invalid action")
            self.run(user_management=user_management, event_list=event_list)

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
        required_attributes = "name:XXX,date:yyyy-mm-dd,venue:XXX,total_seats:XXX,available_seats:XXX,price:float"
        print(required_attributes)
        event_data = input("Enter event data: ")
        event_attr_dict = self.__get_dict_from_string(required_attributes=required_attributes, string=event_data)
        event_attr_dict["event_id"] = id
        event_list.events.append(Event(**event_attr_dict))
        return id

    def delete_event(self, event_list: EventList, **kwargs) -> str:
        id = input("Enter id of event to delete: ")
        result = event_list.delete_event(id, is_admin=self.__is_admin)
        return True

    def edit_event(self, event_list: EventList, **kwargs) -> str:
        pass

    def create_user(self, user_management: UsersManagement, **kwargs) -> str:
        print("Potrzebne dane:")
        id = str(uuid4())
        required_attributes = "login:XXX,password:XXX,email:XXX,data_urodzenia:yyyy-mm-dd"
        print(required_attributes)
        user_data = input("Enter event data: ")
        user_attr_dict = self.__get_dict_from_string(required_attributes=required_attributes, string=user_data)
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
        self, event_list: EventList, user_management: UsersManagement, **kwargs
    ) -> bool:
        user_login = input("Enter login of user: ")
        event_id = input("Enter id of event: ")
        user = user_management.users.get(user_login)
        if user:
            result = event_list.cancel_booking(user, event_id)
        return True

    def edit_booking(
        self, event_list: EventList, user_management: UsersManagement, **kwargs
    ) -> str:
        pass

    def add_booking(
        self, event_list: EventList, user_management: UsersManagement, **kwargs
    ) -> bool:
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

    admin.run(user_management=user_management, event_list=event_list)
