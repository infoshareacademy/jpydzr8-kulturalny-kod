import json
import os
from sys import stdout
from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from tqdm import tqdm


class Command(BaseCommand):
    help = "Load users from JSON file into auth_user"

    def handle(self, *args, **kwargs):
        self._load_users(file_name="users.json")
        self._load_users(file_name="admins.json")
        
    def _load_users(self, file_name: str, *args, **kwargs):
        file_path = os.path.join(settings.BASE_DIR, "apps", "users", "media", "json_files", file_name)
        
        with open(file_path, "r", encoding="utf-8") as f:
            users_json = json.load(f)
        
        users = users_json["users"]

        total_created = 0
        existing_usernames = set(User.objects.values_list("username", flat=True))
        
        for i, user_data in enumerate(
            tqdm(users, desc="Loading users", file=stdout, mininterval=0.5), 
            start=1
        ):
            if user_data["username"] not in existing_usernames:
                User.objects.create_user(
                    first_name=user_data["first_name"],
                    last_name=user_data["last_name"],
                    username=user_data["username"],
                    password=user_data["password"],
                    email=user_data["email"],
                    is_superuser=user_data["is_superuser"],
                    is_staff=user_data["is_staff"],
                    is_active=user_data["is_active"]
                )
                total_created += 1

        self.stdout.write(
            self.style.SUCCESS(f"✅ Created {total_created} users (bulk insert) from file {file_path}.")
        )
