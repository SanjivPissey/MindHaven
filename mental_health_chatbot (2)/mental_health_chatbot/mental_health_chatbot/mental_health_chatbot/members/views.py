from django.shortcuts import get_object_or_404, redirect, render
from django.http import  HttpResponseRedirect
from .models import Assignment, Contact, CustomUser, MoodInsight, Report, UserMood, Message
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.urls import reverse
from django.utils.html import strip_tags
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.urls import reverse
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.utils import timezone
import google.generativeai as genai

# Create your views here.
def home(request):
    return render(request, 'home.html')

def register(request):
    if request.method == 'POST':
        role = request.POST.get('user_type')
        if role == 'psychologist':
            return render(request, 'psychologistregister.html')
        elif role == 'user':
            return render(request, 'userregister.html')
    return render(request, 'register.html')

def psychologistregister(request):
    if request.method == 'POST':
        username=request.POST['username']
        password=request.POST['password']
        email=request.POST['email']
        user= CustomUser.objects.create(username=username, email=email, password=make_password(password), role='psychologist')
        return redirect('user_login')
    else:
        return render(request, 'psychologistregister.html')
    
    
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from .models import CustomUser  # Your custom user model

def user_login(request):
    if request.method == 'POST':
        email = request.POST.get('username')  # Input field holds email
        password = request.POST.get('password')

        try:
            # Fetch user with that email
            user_obj = CustomUser.objects.get(email=email)
            user = authenticate(request, username=user_obj.username, password=password)
        except CustomUser.DoesNotExist:
            user = None

        if user is not None:
            login(request, user)
            if user.role.lower() == 'admin':
                return redirect('admindashboard')
            elif user.role.lower() == 'user':
                return redirect('userdashboard')
            elif user.role.lower() == 'psychologist':
                return redirect('psychologist_dashboard')
            else:
                return redirect('default_dashboard')  # Fallback

        return render(request, 'login.html', {'error_message': 'Invalid username or password.'})

    return render(request, 'login.html')


    
def admindashboard(request):
    user=request.user
    
    if not user.role == 'admin':
        return redirect('no_access')
    
    context={
        'user':user
    }
    return render(request, 'admindashboard.html', context)
    
def userdashboard(request):
    user = request.user
    
    if not user.role == 'user':
        return redirect('no_access')
    
    context = {
        'user': user,
    }
    return render(request, 'userdashboard.html', context)

from django.shortcuts import render

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Assignment, MentalHealthSurvey, Report

@login_required
def psychologist_dashboard(request):
    if request.user.role != 'psychologist':
        return redirect('home')  # redirect if not a psychologist

    # Count assigned users
    assigned_user_count = Assignment.objects.filter(psychologist=request.user).count()

    # Get assigned users
    assigned_users = CustomUser.objects.filter(
        assignments__psychologist=request.user
    ).prefetch_related('usermood_set')
    
    # Add latest mood to each user
    for user in assigned_users:
        latest_mood = UserMood.objects.filter(user=user).order_by('-created_at').first()
        user.latest_mood = latest_mood.mood if latest_mood else 'Not available'
        
        # Get latest mood insight with confidence score
        latest_insight = MoodInsight.objects.filter(user=user).order_by('-created_at').first()
        user.latest_mood_confidence = latest_insight.confidence_score if latest_insight else None

    # Count surveys related to assigned users
    assigned_user_ids = Assignment.objects.filter(psychologist=request.user).values_list('user', flat=True)
    survey_count = MentalHealthSurvey.objects.filter(user__in=assigned_user_ids).count()

    # Count chat messages from assigned users
    chat_count = Message.objects.filter(user__in=assigned_user_ids).count()

    # Count reports created by this psychologist
    report_count = Report.objects.filter(psychologist=request.user).count()

    context = {
        'assigned_user_count': assigned_user_count,
        'assigned_users': assigned_users,
        'survey_count': survey_count,
        'chat_count': chat_count,
        'report_count': report_count,
    }
    return render(request, 'psychologistdashboard.html', context)





def user_logout(request):
    logout(request)
    return redirect('user_login')

def no_access(request):
    return render(request, 'no_access.html')

def contact_view(request):
    if request.method == 'POST':
        try:
            # Get form data
            name = request.POST.get('name')
            email = request.POST.get('email')
            subject = request.POST.get('subject')
            message = request.POST.get('message')
            
            # Validate required fields
            if not all([name, email, subject, message]):
                messages.error(request, "All fields are required!")
                return HttpResponseRedirect('/userdashboard/#contact')
            
            # Save to database
            contact = Contact.objects.create(
                name=name,
                email=email,
                subject=subject,
                message=message
            )
            
            # Send email to admin
            admin_subject = f"New Contact Message: {subject}"
            admin_message = f"""
            You have received a new contact message:
            
            From: {name} ({email})
            Subject: {subject}
            Message:
            {message}
            
            """
            send_mail(
                admin_subject,
                admin_message,
                settings.DEFAULT_FROM_EMAIL,
                [settings.ADMIN_EMAIL],
                fail_silently=False,
            )
            
            # Send confirmation email to user
            user_subject = "Thank you for contacting us"
            html_message = render_to_string('emails/contact_confirmation.html', {
                'name': name,
                'subject': subject,
                'message': message,
            })
            plain_message = strip_tags(html_message)
            
            send_mail(
                user_subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                html_message=html_message,
                fail_silently=False,
            )
            print("Your message has been sent successfully! We'll get back to you soon.")
            messages.success(request, "Your message has been sent successfully! We'll get back to you soon.")
            
            return HttpResponseRedirect('/userdashboard/#contact')
            
        except Exception as e:
            print(f"Error: {str(e)}")
            messages.error(request, "There was an error sending your message. Please try again.")
            return HttpResponseRedirect('/userdashboard/#contact')
    
    return render(request, 'userdashboard.html')

import google.generativeai as genai
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.utils import timezone
from .models import UserMood
from datetime import timedelta

genai.configure(api_key="AIzaSyAUMWuuYsY8E1_cIVzxxr0zN4ViMofw1L4")

def detect_mood(message):
    message = message.lower()
    if any(word in message for word in ['anxious', 'worried', 'panic']):
        return "Anxious"
    elif any(word in message for word in ['sad', 'depressed', 'low']):
        return "Sad"
    elif any(word in message for word in ['okay', 'fine', 'neutral']):
        return "Neutral"
    elif any(word in message for word in ['relaxed', 'calm', 'peaceful']):
        return "Calm"
    elif any(word in message for word in ['happy', 'excited', 'great']):
        return "Happy"
    else:
        return "Neutral"

def detect_stress_level(message):
    message = message.lower()
    if any(word in message for word in ['panic', 'stressed', 'anxious', 'pressure']):
        return 5
    elif any(word in message for word in ['worried', 'overwhelmed']):
        return 4
    elif any(word in message for word in ['fine', 'meh']):
        return 3
    elif any(word in message for word in ['calm', 'relaxed']):
        return 2
    elif any(word in message for word in ['peaceful', 'chill']):
        return 1
    return 3


def home(request):
    return render(request, "home.html")

from django.shortcuts import render

# Sample list of mental health tips
MENTAL_HEALTH_TIPS = [
    "🌞 Start your day with gratitude. One small positive thought can change your whole day!",
    "🌱 Your mind is like a garden. Water it with positive thoughts!",
    "☁️ Don't believe everything you think. Thoughts are not facts—be kind to yourself!",
    "💙 You are enough, just as you are. Take a moment to appreciate yourself today.",
    "🧘 Breathe in courage, breathe out fear. You got this!",
    "📖 Learn something new today! A small step toward growth is still progress.",
    "🏆 Don't compare your progress to others. Focus on being 1% better than yesterday!",
    "🕰️ Take a deep breath. Rushing won't make time move slower—stay present.",
    "🚀 Mistakes are proof you're trying. Every setback is a setup for a comeback!",
    "🛠️ Your mental health matters as much as your success. Prioritize yourself!",
    "🍵 Take a break. Sip some tea. Pause. You deserve rest too!",
    "🎶 Listen to your favorite song today—music heals the soul!",
    "🌸 Treat yourself with the same kindness you show others.",
    "🚶 A short walk can do wonders for your mind. Step outside and breathe!",
    "💌 Write yourself a kind note today. Future-you will thank you!"
]

# Updated section data for rendering the page
SECTION_DATA = {
    "mental_health_tips": {
        "title": "Daily Mental Health Tips",
        "tips": MENTAL_HEALTH_TIPS,  # Pass all tips to the template
        "animation": "fade-in"
    }
}

# View function to render the AI chat page
def ai_chat_page(request, section):
    """Render the AI chat page displaying all mental health tips."""
    # Fetch the section data based on the 'section' argument, if applicable
    if section == 1:
        # You can customize what section 1 refers to (e.g., mental health tips)
        section_data = SECTION_DATA["mental_health_tips"]
    else:
        # Handle other sections or default behavior here
        section_data = SECTION_DATA["mental_health_tips"]

    return render(
        request,
        "ai_chat_page.html",
        {"section_data": section_data}
    )

from django.shortcuts import render

def exercises_and_yoga(request):
    section_data = {
        'title': 'Exercises and Yoga Tips',
        'tips': [
            'Do regular stretches for flexibility.',
            'Practice yoga to improve strength and balance.',
            'Take time for deep breathing exercises.',
            'Incorporate strength training for muscle tone.',
            'Practice mindfulness with yoga for mental clarity.',
        ],
    }
    return render(request, 'exercises_and_yoga.html', {'section_data': section_data})

from django.shortcuts import render

def exercises_and_yoga_tips(request):
    return render(request, 'exercises_and_yoga_tips.html')

from django.shortcuts import render
from django.conf import settings

from django.shortcuts import render

def music_therapy(request):
    music_tips = [
        "🎵 Listen to calming instrumental music before bed.",
        "🎸 Play a musical instrument to relieve stress.",
        "🎶 Create a playlist of your favorite uplifting songs.",
        "🧘‍♀️ Try sound therapy with Tibetan singing bowls.",
        "🎤 Singing along to music can improve your mood instantly.",
        "🎧 Use noise-canceling headphones to focus better while working."
    ]
    return render(request, 'music_therapy.html', {'music_tips': music_tips})


from django.shortcuts import render

# AI-based emotion analysis (simple mapping for now)
def analyze_emotion(emotion):
    coping_strategies = {
        "stressed": [
            "🧘 Try deep breathing exercises to relax.",
            "🎶 Listen to calming music for stress relief.",
            "🌿 Take a short walk in nature.",
            "📖 Read a book or engage in a hobby."
        ],
        "anxious": [
            "☕ Reduce caffeine and hydrate well.",
            "📓 Try writing down your thoughts in a journal.",
            "🎧 Listen to guided meditations.",
            "🏃 Engage in light physical exercise to release tension."
        ],
        "sad": [
            "📞 Talk to a trusted friend or family member.",
            "🍫 Treat yourself with something you love (food, movie, etc.).",
            "🌅 Go out and get some sunlight.",
            "🎨 Try an art therapy activity to express yourself."
        ],
        "happy": [
            "🎉 Celebrate your happiness! Share it with others.",
            "🎶 Make a playlist of your favorite feel-good songs.",
            "❤️ Express gratitude and write down what makes you happy.",
            "📸 Capture the moment in a journal or photo."
        ],
        "tired": [
            "💤 Ensure you're getting enough sleep.",
            "🥗 Eat a nutritious meal for an energy boost.",
            "🚶 Take short breaks and stretch.",
            "🛀 Try a warm bath or relaxation techniques."
        ]
    }
    return coping_strategies.get(emotion.lower(), ["🌟 Stay positive and take care of yourself!"])

# View function for the coping strategies page
def coping_strategies(request):
    user_emotion = request.GET.get('emotion', '')  # Get emotion from query parameters
    tips = analyze_emotion(user_emotion) if user_emotion else []
    
    return render(request, 'coping_strategies.html', {'user_emotion': user_emotion, 'tips': tips})

from django.shortcuts import render, redirect
import google.generativeai as genai
import random

genai.configure(api_key="AIzaSyAUMWuuYsY8E1_cIVzxxr0zN4ViMofw1L4")

MOOD_PROMPTS = {
    "stress": "The user is feeling stressed. Give 3 short therapy tips like book blurbs with relevant emojis. Keep tone soft and comforting.",
    "anxiety": "The user is anxious. Share 3 short, book-style calming tips with soothing emojis. Avoid mentioning medication or doctors.",
    "sadness": "The user feels sad. Suggest 3 kind and gentle book-style blurbs to lift mood with cute or heartwarming emojis.",
    "anger": "The user is angry. Share 3 peaceful, constructive blurbs with gentle emojis to handle anger positively.",
    "tired": "The user is exhausted. Recommend 3 short recharging tips with cozy emojis like tea, moon, or rest icons.",
    "boredom": "The user is bored. Suggest 3 creative and fun mini tips with cheerful, bright emojis."
}

EMOJI_POOL = ["📖", "🌸", "💡", "🌱", "💖", "😌", "☀️", "🌼", "🧘", "🎨", "🫶", "🌈", "📚", "🧠", "🪴"]

def therapy_suggestions(request):
    if request.method == "POST":
        selected_mood = request.POST.get("mood", "").strip().lower()
        request.session["selected_mood"] = selected_mood
        return redirect("/therapy-suggestions/")

    therapy = {}
    selected_mood = request.session.pop("selected_mood", "")

    if selected_mood in MOOD_PROMPTS:
        try:
            prompt = MOOD_PROMPTS[selected_mood]
            model = genai.GenerativeModel("gemini-2.0-flash")
            response = model.generate_content(prompt)
            suggestions = response.text.strip().split('\n')
            clean_suggestions = [s.strip("-•*1234567890. ").strip() for s in suggestions if s.strip()]
            emoji_suggestions = [f"{random.choice(EMOJI_POOL)} {tip}" for tip in clean_suggestions[:3]]
            therapy[selected_mood.capitalize()] = emoji_suggestions
        except Exception as e:
            therapy["Error"] = [f"Could not fetch suggestions: {e}"]

    return render(request, "therapy_suggestions.html", {"therapy": therapy})

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import MentalHealthSurvey, Assignment, CustomUser
import google.generativeai as genai

genai.configure(api_key="AIzaSyAUMWuuYsY8E1_cIVzxxr0zN4ViMofw1L4")

@login_required
def survey_form(request):
    if request.method == "POST":
        survey = MentalHealthSurvey.objects.create(
            user=request.user,
            anxiety_level=request.POST.get('anxiety_level'),
            trauma_experience=request.POST.get('trauma_experience'),
            relationship_issues=request.POST.get('relationship_issues'),
            sleep_quality=request.POST.get('sleep_quality'),
            appetite_change=request.POST.get('appetite_change'),
            energy_level=request.POST.get('energy_level'),
            emotional_control=request.POST.get('emotional_control'),
            social_interaction=request.POST.get('social_interaction'),
            past_mental_health=request.POST.get('past_mental_health'),
            specific_concern=request.POST.get('specific_concern')
        )

        prompt = f"""
        (your full GPT prompt here...)
        """

        try:
            model = genai.GenerativeModel("gemini-2.0-flash")
            response = model.generate_content(prompt)
            suggested_psychologist_name = response.text.strip()

            psychologist_user = CustomUser.objects.get(fullname__icontains=suggested_psychologist_name, role='psychologist')

            Assignment.objects.create(user=request.user, psychologist=psychologist_user)

            # THIS IS CORRECT: DIRECT RENDER
            return render(request, "thank_you.html", {"psychologist_name": suggested_psychologist_name})

        except Exception as e:
            print("Error:", e)
            return redirect('survey_form')  # Optional fallback

    return render(request, "survey_form.html")


def thank_you(request):
    return render(request, "thank_you.html")

from django.http import JsonResponse 
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def chatbot(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_query = data.get('query', '').lower()

            responses = {
                "hello": "Hi there! I'm here for you. How can I help?",
                "hi": "Hello! I'm listening. 😊",
                "sad": "I'm sorry you're feeling that way. Do you want to talk more about it?",
                "anxious": "Anxiety can be tough. I'm here with you. Would you like to try a breathing exercise?",
                "depressed": "You're not alone. I'm here to support you. Would you like to speak to a counselor?",
                "bye": "Take care! Remember, you're not alone.",
                "thank you": "You're welcome! Anytime 💙"
            }

            bot_response = "I'm here to support you, but I didn't quite catch that. Could you rephrase?"

            for key in responses:
                if key in user_query:
                    bot_response = responses[key]
                    break

            return JsonResponse({'response': bot_response})

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)

from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def profile_view(request):
    user = request.user
    return render(request, 'profile.html', {
        'user': user,
    })

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

@login_required
def feedback_view(request):
    if request.method == 'POST':
        feedback = request.POST.get('feedback')
        # You can store feedback to the database later
        print("Received feedback:", feedback)  # for now, just print to console
        return render(request, 'feedback_thanks.html')
    return render(request, 'feedback.html')

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import UserMood




from django.shortcuts import render
from django.http import JsonResponse
from datetime import datetime, timedelta

# Fake mood data (replace with DB data in real app)
MOOD_MAP = ["Calm", "Anxious", "Sad", "Neutral", "Happy"]
MOOD_SCORES = {"Happy": 5, "Calm": 4, "Neutral": 3, "Sad": 2, "Anxious": 1}

def mood_insights_dashboard(request):
    return render(request, 'mood_dashboard.html')

from django.http import JsonResponse
from datetime import timedelta
from .models import UserMood

MOOD_MAP = {"Happy": 5, "Calm": 4, "Neutral": 3, "Sad": 2, "Anxious": 1}

def get_mood_data(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    today = timezone.now().date()
    last_7_days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    labels = [day.strftime('%a') for day in last_7_days]

    entries = UserMood.objects.filter(user=request.user, created_at__in=last_7_days)
    mood_by_date = {e.created_at: e.mood for e in entries}

    moods = [mood_by_date.get(day, "Neutral") for day in last_7_days]
    scores = [MOOD_MAP.get(m, 3) for m in moods]

    streak = sum(1 for m in reversed(moods) if m == "Calm")
    top_emotion = max(set(moods), key=moods.count) if moods else "Neutral"

    return JsonResponse({
        "labels": labels,
        "scores": scores,
        "streak": streak,
        "top_emotion": top_emotion,
        "suggestion": "You're doing great! Keep checking in and maintaining your calm 💙"
    })


from django.shortcuts import render, redirect
from members.models import CustomUser
from django.contrib import messages

def userregister(request):
    if request.method == 'POST':
        fullname = request.POST['fullname']
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']

        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return redirect('userregister')
        elif CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            return redirect('userregister')
        else:
            user = CustomUser.objects.create_user(
                username=username,
                email=email,
                password=password,
            )
            user.fullname = fullname
            user.role = 'user'  # Optional: set role explicitly
            user.save()
            messages.success(request, 'Registration successful. Please log in.')
            return redirect('user_login')  # Make sure this matches your URL name

    return render(request, 'userregister.html')


def forgot_password(request):
    if request.method == "POST":
        email = request.POST.get('email')
        try:
            user = CustomUser.objects.get(email=email)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_link = request.build_absolute_uri(
                reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
            )
            message = render_to_string('emails/password_reset_email.html', {
                'user': user,
                'reset_link': reset_link
            })
            send_mail(
                subject="Password Reset Request",
                message=message,
                from_email="themindeaseteam@gmail.com",
                recipient_list=[email]
            )
            messages.success(request, "A reset link has been sent to your email.")
        except CustomUser.DoesNotExist:
            messages.error(request, "No account found with this email.")
        return redirect('forgot_password')

    return render(request, 'forgot_password.html')


@login_required
def view_survey(request, user_id):
    survey = get_object_or_404(MentalHealthSurvey, id=user_id)
    return render(request, 'view_survey.html', {'survey': survey})

@login_required
def create_report(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        summary = request.POST.get('summary')
        recommendations = request.POST.get('recommendations')

        if user_id:
            user = get_object_or_404(CustomUser, id=user_id)
            
            # Check if this user is assigned to the psychologist
            if not Assignment.objects.filter(user=user, psychologist=request.user).exists():
                messages.error(request, "You don't have access to this user's data.")
                return redirect('assigned_users')
            
            summary
            recommendations

            Report.objects.create(
                user=user,
                psychologist=request.user,
                summary=summary,
                recommendations=recommendations,
            )
            messages.success(request, f"Report for {user.fullname} created successfully.")
            return redirect('assigned_users')
        else:
            messages.error(request, "User ID is required.")
            return redirect('assigned_users')

    # Get user_id from the query string if provided (from chat history page)
    user_id = request.GET.get('user_id')
    user = None
    chat_messages = None
    
    if user_id:
        try:
            user = CustomUser.objects.get(id=user_id)
            # Check if user is assigned to this psychologist
            if Assignment.objects.filter(user=user, psychologist=request.user).exists():
                # Get chat messages for context
                chat_messages = Message.objects.filter(user=user).order_by('-created_at')[:20]
            else:
                messages.error(request, "You don't have access to this user's data.")
                return redirect('assigned_users')
        except CustomUser.DoesNotExist:
            messages.error(request, "User not found.")
            return redirect('assigned_users')

    return render(request, 'generate_report.html', {
        'user': user,
        'chat_messages': chat_messages
    })

# Edit an Existing Report
@login_required
def edit_report(request, report_id):
    report = get_object_or_404(Report, id=report_id, psychologist=request.user)

    if request.method == 'POST':
        summary = request.POST.get('summary')
        recommendations = request.POST.get('recommendations')

        report.content = f"Summary:\n{summary}\n\nRecommendations:\n{recommendations}"
        report.save()
        return redirect('assigned_users')

    return render(request, 'edit_report.html', {'report': report})

# View All Reports
@login_required
def view_reports(request):
    if request.user.role != 'psychologist':
        return redirect('home')
        
    # Get assigned users
    assigned_users = CustomUser.objects.filter(
        assignments__psychologist=request.user
    )
    
    # Get reports created by this psychologist
    reports = Report.objects.filter(psychologist=request.user).select_related('user').order_by('-created_at')
    
    return render(request, 'view_report.html', {
        'reports': reports,
        'assigned_users': assigned_users
    })

@login_required
def assigned_users(request):
    if request.user.role != 'psychologist':
        return redirect('userdashboard')  # Only psychologist can access

    # Fetch all users assigned to this psychologist
    assigned = Assignment.objects.filter(psychologist=request.user).select_related('user')

    return render(request, 'assigned_users.html', {'assigned_users': assigned})


from .models import MentalHealthSurvey, CustomUser, Assignment

import google.generativeai as genai

genai.configure(api_key="AIzaSyAUMWuuYsY8E1_cIVzxxr0zN4ViMofw1L4")  # Add your real API key

def assign_psychologist_based_on_survey(survey_instance):
    """Use Gemini/GPT to recommend psychologist based on survey answers."""
    prompt = (
        f"Analyze the following user's mental health survey:\n\n"
        f"Anxiety Level: {survey_instance.anxiety_level}\n"
        f"Trauma Experience: {survey_instance.trauma_experience}\n"
        f"Relationship Issues: {survey_instance.relationship_issues}\n"
        f"Sleep Quality: {survey_instance.sleep_quality}\n"
        f"Appetite Change: {survey_instance.appetite_change}\n"
        f"Energy Level: {survey_instance.energy_level}\n"
        f"Emotional Control: {survey_instance.emotional_control}\n"
        f"Social Interaction: {survey_instance.social_interaction}\n"
        f"Past Mental Health: {survey_instance.past_mental_health}\n"
        f"Specific Concern: {survey_instance.specific_concern}\n\n"
        f"Based on the symptoms, suggest which area this person needs help with: \n"
        f"- Trauma, Relationships, Anxiety, Sleep, or General Mental Health\n"
        f"Just respond with one word or short phrase."
    )
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(prompt)
    specialization = response.text.strip().lower()

    # Get all psychologists from the database
    psychologists = CustomUser.objects.filter(role='psychologist')
    
    # If no psychologists exist, return None
    if not psychologists.exists():
        return None
        
    # Match based on specialization - adjust the names to match your actual psychologists
    if "trauma" in specialization:
        return psychologists.filter(fullname__icontains="Smith").first() or psychologists.first()
    elif "relationship" in specialization:
        return psychologists.filter(fullname__icontains="Alice").first() or psychologists.first()
    elif "anxiety" in specialization:
        return psychologists.filter(fullname__icontains="John").first() or psychologists.first()
    elif "sleep" in specialization:
        return psychologists.filter(fullname__icontains="Emma").first() or psychologists.first()
    else:
        # Return a random psychologist if no match
        return psychologists.order_by('?').first()

def submit_survey(request):
    if request.method == "POST":
        anxiety_level = request.POST.get('anxiety_level')
        trauma_experience = request.POST.get('trauma_experience')
        relationship_issues = request.POST.get('relationship_issues')
        sleep_quality = request.POST.get('sleep_quality')
        appetite_change = request.POST.get('appetite_change')
        energy_level = request.POST.get('energy_level')
        emotional_control = request.POST.get('emotional_control')
        social_interaction = request.POST.get('social_interaction')
        past_mental_health = request.POST.get('past_mental_health')
        specific_concern = request.POST.get('specific_concern')
        
        # Create survey instance
        survey = MentalHealthSurvey.objects.create(
            user=request.user,
            anxiety_level=anxiety_level,
            trauma_experience=trauma_experience,
            relationship_issues=relationship_issues,
            sleep_quality=sleep_quality,
            appetite_change=appetite_change,
            energy_level=energy_level,
            emotional_control=emotional_control,
            social_interaction=social_interaction,
            past_mental_health=past_mental_health,
            specific_concern=specific_concern
        )

        # Get psychologist based on survey
        psychologist = assign_psychologist_based_on_survey(survey)

        if psychologist:
            # Create assignment
            Assignment.objects.create(user=request.user, psychologist=psychologist)
            psychologist_name = psychologist.fullname
        else:
            # If no psychologist found, use a default message
            psychologist_name = "a mental health professional"

        return render(request, "thank_you.html", {"psychologist_name": psychologist_name})
    
    return render(request, "survey_form.html")

@login_required
def view_survey(request):
    survey = MentalHealthSurvey.objects.all().first()
    return render(request, 'view_survey.html', {'survey': survey})


from .models import UserMood
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
import google.generativeai as genai

@csrf_exempt
def ai_chat_support(request):
    if request.method == 'POST':
        try:
            user_message = request.POST.get('user_message', '').strip()
            if not user_message:
                return JsonResponse({'error': 'Message is empty.'}, status=400)

            # Detect mood and stress
            mood = detect_mood(user_message)
            stress = detect_stress_level(user_message)

            if request.user.is_authenticated:
                # Save or update user mood
                UserMood.objects.update_or_create(
                    user=request.user,
                    created_at=timezone.now().date(),
                    defaults={'mood': mood, 'stress_level': stress}
                )
                
                # Save user's message
                Message.objects.create(
                    user=request.user,
                    sender='user',
                    text=user_message,
                    created_at=now()
                )

            # Generate AI reply
            prompt = (
                f"You are a supportive therapist. A user says: '{user_message}'. "
                "Reply with 3-4 comforting, empathetic, and supportive sentences. "
                "Avoid repeating the user's message and do not ask questions. Just provide emotional reassurance."
            )

            try:
                model = genai.GenerativeModel("gemini-2.0-flash")
                response = model.generate_content(prompt)
                ai_reply = response.text.strip() if response and response.text else "I'm here for you. Everything will be okay 💙"
            except Exception as e:
                # Fallback responses if API fails
                ai_reply = "I'm here to support you. Everything will be okay. Remember to be kind to yourself during difficult times."
                
            # Save bot's reply if user is authenticated
            if request.user.is_authenticated:
                Message.objects.create(
                    user=request.user,
                    sender='bot',
                    text=ai_reply,
                    created_at=now()
                )

            return JsonResponse({'ai_reply': ai_reply}, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return render(request, 'ai_chat_support.html')

@login_required
def chat_history(request, user_id=None):
    if not request.user.role == 'psychologist':
        return redirect('home')
    
    # Get assigned users for the psychologist
    assigned_users = CustomUser.objects.filter(
        assignments__psychologist=request.user
    )
    
    if user_id:
        try:
            selected_user = CustomUser.objects.get(id=user_id)
            # Verify this user is assigned to the psychologist
            if not Assignment.objects.filter(user=selected_user, psychologist=request.user).exists():
                messages.error(request, "You don't have access to this user's data.")
                return redirect('chat_history')
            
            # Get chat messages for the selected user
            chat_messages = Message.objects.filter(user=selected_user).order_by('created_at')
            
            return render(request, 'chat_history.html', {
                'selected_user': selected_user,
                'messages': chat_messages
            })
        except CustomUser.DoesNotExist:
            messages.error(request, "User not found.")
            return redirect('chat_history')
    
    return render(request, 'chat_history.html', {
        'assigned_users': assigned_users
    })

# views.py

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Report  # Replace with your actual model

@login_required
def user_report_view(request):
    user = request.user
    user_report = Report.objects.filter(user=user).order_by('-created_at').first()  # Latest report
    return render(request, 'user/user_report.html', {'report': user_report})
