from django.contrib import admin

# Register your models here.

from .models import UserMood, Message
admin.site.register(UserMood)
admin.site.register(Message)
