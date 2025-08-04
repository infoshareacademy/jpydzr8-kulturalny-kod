import json
import os
from sys import stdout
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.conf import settings
from tqdm import tqdm

class Command(BaseCommand):
    help = "Load users from JSON file into auth_user"
    
    def add_arguments(self, parser):
        parser.add_argument('--batch-size', type=int, default=1000)

    def handle(self, *args, **kwargs):
        batch_size = kwargs["batch_size"]
        self._load_users(file_name="users.json", batch_size=batch_size)
        self._load_users(file_name="admins.json", batch_size=batch_size)
        
    def _load_users(self, file_name: str, batch_size: int = 1000, *args, **kwargs):
        
        file_path = os.path.join(settings.BASE_DIR, "data", file_name)
        
        with open(file_path, "r", encoding="utf-8") as f:
            users_json = json.load(f)
        
        new_users = []
        users = users_json["users"]

        total_created = 0
        existing_usernames = set(User.objects.values_list("username", flat=True))
        
        for i, user_data in enumerate(
            tqdm(users, desc="Loading users", file=stdout, mininterval=0.5), 
            start=1
        ):
            if user_data["username"] not in existing_usernames:
                new_users.append(
                    User(
                        first_name=user_data["first_name"],
                        last_name=user_data["last_name"],
                        username=user_data["username"],
                        password=make_password(user_data["password"]),  # ✅ hash before insert
                        email=user_data["email"],
                        is_superuser=user_data["is_superuser"],
                        is_staff=user_data["is_staff"],
                        is_active=user_data["is_active"]
                    )
                )

            if i % batch_size == 0:
                User.objects.bulk_create(new_users, ignore_conflicts=True)
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Batch {i // batch_size}. Created {len(new_users)} users (bulk insert) from file {file_path}.")
                )
                total_created += len(new_users)
                new_users.clear()
        if new_users:
            User.objects.bulk_create(new_users, ignore_conflicts=True)
            total_created += len(new_users)

        self.stdout.write(
            self.style.SUCCESS(f"✅ Created {total_created} users (bulk insert) from file {file_path}.")
        )
