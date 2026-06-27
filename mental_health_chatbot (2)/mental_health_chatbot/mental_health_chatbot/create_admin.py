
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mental_health_chatbot.settings')
django.setup()

from members.models import CustomUser

username = 'admin'
email = 'admin@example.com'
password = 'password123'

if not CustomUser.objects.filter(username=username).exists():
    CustomUser.objects.create_superuser(username=username, email=email, password=password)
    print(f"Superuser '{username}' created successfully.")
else:
    print(f"Superuser '{username}' already exists.")
