from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

# Custom User
class CustomUser(AbstractUser):
    USER_TYPE = [
        ('admin', 'Admin'),
        ('user', 'User'),
        ('psychologist', 'Psychologist'),
    ]
    fullname = models.CharField(max_length=255, default='null')
    role = models.CharField(max_length=15, choices=USER_TYPE, default='user')
    specialty = models.CharField(max_length=50, blank=True, null=True)

    @property
    def is_psychologist(self):
        return self.role == 'psychologist'

# Contact Model
class Contact(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()

    def __str__(self):
        return self.name

# Mental Health Survey
class MentalHealthSurvey(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    anxiety_level = models.CharField(max_length=20)
    trauma_experience = models.CharField(max_length=10)
    relationship_issues = models.CharField(max_length=10)
    sleep_quality = models.CharField(max_length=20)
    appetite_change = models.CharField(max_length=20)
    energy_level = models.CharField(max_length=20)
    emotional_control = models.CharField(max_length=10)
    social_interaction = models.CharField(max_length=20)
    past_mental_health = models.CharField(max_length=10)
    specific_concern = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Survey by {self.user.username} on {self.submitted_at.strftime('%Y-%m-%d')}"

# Assignment (user -> psychologist)
class Assignment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='assignments')
    psychologist = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='assigned_users')
    assigned_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} assigned to {self.psychologist.username}"

# Appointment
class Appointment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_appointments')
    psychologist = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='psychologist_appointments')
    date = models.DateField()
    time = models.TimeField()
    status = models.CharField(max_length=20, choices=[('Scheduled', 'Scheduled'), ('Completed', 'Completed'), ('Cancelled', 'Cancelled')], default='Scheduled')
    meet_link = models.URLField(max_length=500, blank=True, null=True)
    reminder_24h_sent = models.BooleanField(default=False)
    reminder_1h_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Appointment: {self.user.username} with {self.psychologist.username} on {self.date} at {self.time}"

# User Profile
class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.CharField(max_length=15)
    role = models.CharField(max_length=20, default='user')
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)

    def __str__(self):
        return self.full_name


# User Mood
class UserMood(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_moods')
    mood = models.CharField(max_length=50)
    stress_level = models.IntegerField(default=3)
    created_at = models.DateTimeField()

    def __str__(self):
        return f"{self.user.username} - {self.mood} on {self.created_at.strftime('%Y-%m-%d')}"

# Mood Insights
class MoodInsight(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    mood = models.CharField(max_length=50)
    stress_level = models.IntegerField(default=3)
    confidence_score = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"{self.user.username} - {self.mood} ({self.confidence_score})"



class Report(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    psychologist = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='reports_created')
    summary = models.TextField(default='summary')
    recommendations = models.TextField(default='recommendations')  # <-- ADD THIS FIELD
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report for {self.user.fullname} by {self.psychologist.fullname}"
    
class UserFeedback(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    helpful = models.CharField(max_length=50)
    ease_of_use = models.CharField(max_length=50)
    dashboard_feedback = models.CharField(max_length=50)
    satisfaction = models.CharField(max_length=50)
    recommend = models.CharField(max_length=50)
    suggestions = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)



# Notifications
class Notification(models.Model):
    psychologist = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.psychologist.username}"

# Audit Logs
class AuditLog(models.Model):
    psychologist = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.psychologist.username} - {self.action}"

from django.db import models
from django.conf import settings


class Message(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=10, choices=[('user', 'User'), ('bot', 'Bot')])
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        db_table = 'members_message'

    def __str__(self):
        return f"{self.sender}: {self.text[:50]}..."
