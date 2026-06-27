import os
import sys
import django
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

sys.path.append(r'c:\Users\pisse\OneDrive\Desktop\mental_health_chatbot123\mental_health_chatbot (2)\mental_health_chatbot\mental_health_chatbot')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mental_health_chatbot.settings')
django.setup()

channel_layer = get_channel_layer()
# We assume psychologist 1 exists (or we can just send to a dummy group to see if it doesn't crash)
# Actually let's just dispatch to psychologist_1
async_to_sync(channel_layer.group_send)(
    'psychologist_1',
    {
        'type': 'send_notification',
        'message': 'Test notification from script!'
    }
)
print("Notification sent!")
