@echo off
echo Starting Mental Health Chatbot...
cd "mental_health_chatbot (2)\mental_health_chatbot\mental_health_chatbot"
call venv\Scripts\activate
python manage.py runserver
pause
