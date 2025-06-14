if __name__ == "__main__":
    user_list = UserList()
    user_list.load("users.json")

    event_list = EventList()
    event_list.load("events.json")

    start = Start()
    start.run()