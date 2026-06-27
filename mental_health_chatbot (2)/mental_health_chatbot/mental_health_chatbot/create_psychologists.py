
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mental_health_chatbot.settings')
django.setup()

from members.models import CustomUser, UserProfile

psychologists = [
    {"name": "Dr. Emily Carter", "specialization": "Clinical Psychologist", "email": "emily@example.com"},
    {"name": "Dr. Sarah Mitchell", "specialization": "Child Psychologist", "email": "sarah@example.com"},
    {"name": "Dr. James Anderson", "specialization": "Counseling Psychologist", "email": "james@example.com"},
    {"name": "Dr. Amanda Blake", "specialization": "Trauma Specialist", "email": "amanda@example.com"},
]

for psych in psychologists:
    user, created = CustomUser.objects.get_or_create(
        username=psych["name"].replace(" ", "").replace(".", "").lower(),
        defaults={
            "email": psych["email"],
            "fullname": psych["name"],
            "role": "psychologist"
        }
    )
    if created:
        user.set_password("password123")
        user.save()
        UserProfile.objects.create(
            user=user,
            full_name=psych["name"],
            email=psych["email"],
            role="psychologist"
        )
        print(f"Created {psych['name']}")
    else:
        if user.role != 'psychologist':
            user.role = 'psychologist'
            user.fullname = psych['name']
            user.save()
            print(f"Updated {psych['name']} role")
        else:
            print(f"{psych['name']} already exists")

print("Psychologist seeding complete.")
