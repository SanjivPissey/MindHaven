from django.urls import path
from . import views  # Import all your view functions
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),
    path('user_login/', views.user_login, name='user_login'),
    path('register/', views.register, name='register'),
    path('userregister/', views.userregister, name='userregister'),
    path('psychologistregister/', views.psychologistregister, name='psychologistregister'),
    path('admindashboard/', views.admindashboard, name='admindashboard'),
    path('userdashboard/', views.userdashboard, name='userdashboard'),
    path('user_logout/', views.user_logout, name='user_logout'),
    path('no_access/', views.no_access, name='no_access'),
    path('contact_view/', views.contact_view, name='contact_view'),
    
    path('ai-chat-support/', views.ai_chat_support, name='ai_chat_support'),
    path('chat/<int:section>/', views.ai_chat_page, name='ai_chat_page'),
    path('exercises-and-yoga/', views.exercises_and_yoga, name='exercises_and_yoga'),
    path('music-therapy/', views.music_therapy, name='music_therapy'),
    path('coping-strategies/', views.coping_strategies, name='coping_strategies'),
    path('therapy-suggestions/', views.therapy_suggestions, name='therapy_suggestions'),
    path('survey_form/', views.survey_form, name='survey_form'),
    path('thank-you/', views.thank_you, name='thank_you'),
    path('forgot_password/', views.forgot_password, name='forgot_password'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='reset_complete.html'), name='password_reset_complete'),
    path('profile/', views.profile_view, name='profile'),
    path('contact/', views.contact_view, name='contact'),
    path('feedback/', views.feedback_view, name='feedback'),
    path('logout/', views.user_logout, name='logout'),
    path('mood-insights-data/', views.get_mood_data, name='get_mood_data'),
    path('mood-insights-dashboard/', views.mood_insights_dashboard, name='mood_insights_dashboard'),
    path('psychologist_dashboard/', views.psychologist_dashboard, name='psychologist_dashboard'),
    path('assigned_users/', views.assigned_users, name='assigned_users'),
    path('survey/', views.submit_survey, name='submit_survey'),
    path('view_survey/', views.view_survey, name='view_survey'),
    path('generate_report/<int:user_id>/', views.create_report, name='generate_report'),
    path('edit_report/', views.edit_report, name='edit_report'),
    path('reports/', views.view_reports, name='view_reports'),

]