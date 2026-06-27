
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mental_health_chatbot.settings')
django.setup()

from members.models import CustomUser, UserProfile

username = 'testuser'
email = 'testuser@example.com'
password = 'password123'

user, created = CustomUser.objects.get_or_create(
    username=username,
    defaults={
        'email': email,
        'fullname': 'Test User',
        'role': 'user'
    }
)

if created:
    user.set_password(password)
    user.save()
    UserProfile.objects.create(
        user=user,
        full_name='Test User',
        email=email,
        role='user'
    )
    print(f"User '{username}' created successfully.")
else:
    if not user.check_password(password):
        user.set_password(password)
        user.save()
        print(f"User '{username}' password updated.")
    else:
        print(f"User '{username}' already exists and password is correct.")
