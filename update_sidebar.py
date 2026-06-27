import os
import re

directory = r'c:\Users\pisse\OneDrive\Desktop\mental_health_chatbot123\mental_health_chatbot (2)\mental_health_chatbot\mental_health_chatbot\members\templates'
files_to_check = [
    'assigned_users.html', 'psychologist_profile.html', 'chat_history.html', 
    'mood_insights.html', 'reports.html', 'view_survey.html', 
    'psychologist_edit_profile.html'
]

link_to_add = '      <li><a href="/psychologist_appointments/"><i class="fas fa-calendar-alt"></i>Appointments</a></li>\n'

for filename in files_to_check:
    filepath = os.path.join(directory, filename)
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'psychologist_appointments' not in content:
            # We want to insert it after Assigned Users
            new_content = re.sub(
                r'(<li><a href="/assigned_users"><i class="fas fa-users"></i>Assigned Users</a></li>)',
                r'\1\n' + link_to_add,
                content
            )
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f'Updated {filename}')
        else:
            print(f'{filename} already has it')
