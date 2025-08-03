from uuid import uuid4
from random import choices, randint
import random
from datetime import datetime, timedelta
from unidecode import unidecode
import json
import string
import os


# Get the directory where the script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def generate_password(length=12):
    characters = string.ascii_letters + string.digits + string.punctuation
    password = "".join(choices(characters, k=length))
    return password


def generate_data(
    num_users: int = 10000,
    password_length: int = 12,
    oldest_date_of_birth: datetime = datetime(1950, 1, 1),
    seed: int = 42,
    output_file_name: str = "users.json"
) -> None:
    random.seed(seed)
    imiona_link = os.path.join(SCRIPT_DIR, "imiona.txt")
    nazwiska_meskie_link = os.path.join(SCRIPT_DIR, "nazwiska_meskie.txt")
    nazwiska_zenskie_link = os.path.join(SCRIPT_DIR, "nazwiska_zenskie.txt")

    users_list = []
    imiona = []
    imiona_weights = []
    nazwiska_meskie = []
    nazwiska_meskie_weights = []
    nazwiska_zenskie = []
    nazwiska_zenskie_weights = []

    day_to_today = (datetime.now() - oldest_date_of_birth).days

    with open(imiona_link, "r") as imiona_file:
        for i, line in enumerate(imiona_file.readlines()):
            if i > 0:
                line = line.replace("\n", "").split(",")
                imiona.append([line[0].capitalize(), line[1][0].lower()])
                imiona_weights.append(int(line[-1]))

    with open(nazwiska_meskie_link, "r") as nazwiska_meskie_file:
        for i, line in enumerate(nazwiska_meskie_file.readlines()):
            if i > 0:
                line = line.replace("\n", "").split(",")
                nazwiska_meskie.append(line[0].capitalize())
                nazwiska_meskie_weights.append(int(line[-1]))

    with open(nazwiska_zenskie_link, "r") as nazwiska_zenskie_file:
        for i, line in enumerate(nazwiska_zenskie_file.readlines()):
            if i > 0:
                line = line.replace("\n", "").split(",")
                nazwiska_zenskie.append(line[0].capitalize())
                nazwiska_zenskie_weights.append(int(line[-1]))

    for _ in range(num_users):
        user = {}
        imie = choices(imiona, weights=imiona_weights, k=1)[0]
        user["imie"] = imie[0]
        plec = imie[1]
        if plec == "m":
            nazwisko = choices(nazwiska_meskie, weights=nazwiska_meskie_weights, k=1)[0]
        else:
            nazwisko = choices(nazwiska_zenskie, weights=nazwiska_zenskie_weights, k=1)[0]
        user["nazwisko"] = nazwisko
        user["plec"] = plec
        data_urodzenia = datetime.now() - timedelta(days=randint(0, day_to_today))
        user["data_urodzenia"] = str(data_urodzenia.date())
        user["id"] = str(uuid4())
        login = unidecode(
            f"{user['imie'].lower()[0]}.{user['nazwisko'].lower()}{data_urodzenia.year}{user["id"][:2]}"
        )
        user["login"] = login
        user["password"] = generate_password(password_length)
        user["email"] = f"{login}@example.com"
        users_list.append(user)

    json_data = {
        "users": users_list,
        "created_at": str(datetime.now()),
        "num_users": num_users,
        "password_length": password_length,
        "oldest_date_of_birth": str(oldest_date_of_birth),
        "output_file_name": output_file_name,
    }
    with open(os.path.join(SCRIPT_DIR, output_file_name), "w") as output_file:
        json.dump(json_data, output_file, indent=4)


if __name__ == "__main__":
    generate_data()
