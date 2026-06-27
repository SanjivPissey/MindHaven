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
    role = models.CharField(max_length=15, choices=USER_TYPE, default='User')

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

# User Profile
class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.CharField(max_length=15)
    role = models.CharField(max_length=20, default='user')

    def __str__(self):
        return self.full_name

# Used Services
class UsedService(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    service_name = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.service_name}"


# User Mood
class UserMood(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    mood = models.CharField(max_length=50)
    stress_level = models.IntegerField(default=3)
    created_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.mood} on {self.created_at}"

# Mood Insights
class MoodInsight(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    mood = models.CharField(max_length=50)
    confidence_score = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.mood} ({self.confidence_score})"

# Psychologist Reports
class Report(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    psychologist = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='psychologist_reports')
    summary = models.TextField()
    recommedations = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Report by {self.psychologist.username} for {self.user.username}"

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

