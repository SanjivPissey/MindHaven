from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Home & Auth
    path('', views.home, name='home'),
    path('user_login/', views.user_login, name='user_login'),
    path('logout/', views.user_logout, name='logout'),
    path('user_logout/', views.user_logout, name='user_logout'),
    path('forgot_password/', views.forgot_password, name='forgot_password'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='reset_complete.html'), name='password_reset_complete'),

    # Registration
    path('register/', views.register, name='register'),
    path('userregister/', views.userregister, name='userregister'),
    path('psychologistregister/', views.psychologistregister, name='psychologistregister'),

    # Dashboards
    path('userdashboard/', views.userdashboard, name='userdashboard'),
    path('admindashboard/', views.admindashboard, name='admindashboard'),
    path('psychologist_dashboard/', views.psychologist_dashboard, name='psychologist_dashboard'),
    
    # Mood & Insights
    path('mood-dashboard/', views.mood_dashboard, name='mood_dashboard'),
    path('mood-insights-data/', views.get_mood_data, name='get_mood_data'),
    path('mood_insights/', views.mood_insights, name='mood_insights'),
    path('mood_insights/<int:user_id>/', views.mood_insights, name='mood_insights_user'),
    # List of reports (no report_id)
    path('reports/', views.reports_list, name='reports_list'),
    path('user_report/', views.user_report_view, name='user_report_view'),




    # Single report view (with report_id)
    path('view_report/<int:report_id>/', views.view_report, name='view_report'),

    # Reports & Surveys
    path('survey_form/', views.survey_form, name='survey_form'),
    path('survey/', views.submit_survey, name='submit_survey'),
    path('view_survey/', views.view_survey, name='view_survey_list'),
    path('view_survey/<int:user_id>/', views.view_survey, name='view_survey_detail'),
    path('generate_report/<int:user_id>/', views.create_report, name='generate_report'),

    # Chat
    path('ai-chat-support/', views.ai_chat_support, name='ai_chat_support'),
    path('chat/<int:section>/', views.ai_chat_page, name='ai_chat_page'),
    path('chat_history/', views.chat_history, name='chat_history'),
    path('chat_history/<int:user_id>/', views.chat_history, name='chat_history_user'),

    # Activities
    path('exercises-and-yoga/', views.exercises_and_yoga, name='exercises_and_yoga'),
    path('music-therapy/', views.music_therapy, name='music_therapy'),
    path('coping-strategies/', views.coping_strategies, name='coping_strategies'),
    path('therapy-suggestions/', views.therapy_suggestions, name='therapy_suggestions'),

    # Admin Views
    path('admin_user_list/', views.admin_user_list, name='admin_user_list'),
    path('admin_psychologist_list/', views.admin_psychologist_list, name='admin_psychologist_list'),
    path('admin_survey_list/', views.admin_survey_list, name='admin_survey_list'),
    path('admin_contact_messages/', views.admin_contact_messages, name='admin_contact_messages'),
    path('admin_mood_analytics/', views.admin_mood_analytics, name='admin_mood_analytics'),
    path('admin_report_list/', views.admin_report_list, name='admin_report_list'),

    # Profiles
    
    path('psychologist_profile/', views.psychologist_profile, name='psychologist_profile'),
    path('psychologist_edit_profile/', views.psychologist_edit_profile, name='psychologist_edit_profile'),

    # Feedback & Contact
    path('feedback/', views.feedback_view, name='feedback'),
    path('feedback/success/', views.feedback_success, name='feedback_success'),

    path('contact/',views.contact, name="contact"),
     path('contact/', views.contact_view, name='contact_view'),

    # Access Control
    path('no_access/', views.no_access, name='no_access'),

    # Psychologist Assignments
    path('assigned_users/', views.assigned_users, name='assigned_users'),

    # Appointments & Telehealth
    path('book_appointment/', views.book_appointment, name='book_appointment'),
    path('psychologist_appointments/', views.psychologist_appointments, name='psychologist_appointments'),
    path('video_call/<int:appointment_id>/', views.video_call, name='video_call'),
]
