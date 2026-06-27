from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.db import models
from django.db.models import Prefetch, Count
from django.conf import settings

from django.utils import timezone
from datetime import datetime, timedelta
import json
import random
import re
import uuid
import google.generativeai as genai

from .models import (
    CustomUser, MentalHealthSurvey, Assignment, Contact, Report, 
    MoodInsight, UserMood, UserProfile, Message, Appointment, UserFeedback
)
from .forms import MentalHealthSurveyForm, EditProfileForm, FeedbackForm
from .chat_responses import get_rule_based_response, should_use_api
from .dataset_integration import load_examples_from_file, create_few_shot_prompt, get_enhanced_system_prompt
from .services import detect_mood, detect_stress_level, analyze_emotion


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
        username = request.POST['username']
        password = request.POST['password']
        email = request.POST['email']
        full_name = request.POST.get('fullname', username)

        # Check if username or email already exists
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'psychologistregister.html')
        elif CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            return render(request, 'psychologistregister.html')

        # Use create_user() instead of make_password() for proper password hashing
        user = CustomUser.objects.create_user(
            username=username,
            email=email,
            password=password,
            role='psychologist'
        )
        user.fullname = full_name
        user.save()

        UserProfile.objects.create(
            user=user,
            full_name=full_name,
            email=email,
            phone_number='',
            role='psychologist'
        )
        messages.success(request, 'Registration successful. Please log in.')
        return redirect('user_login')
    else:
        return render(request, 'psychologistregister.html')


def user_login(request):
    if request.method == 'POST':
        username_or_email = request.POST.get(
            'username')  # Can be username or email
        password = request.POST.get('password')

        if not username_or_email or not password:
            messages.error(
                request, 'Please provide both username/email and password.')
            return render(request, 'login.html')

        user = None

        # Try to authenticate with username first
        user = authenticate(
            request, username=username_or_email, password=password)

        # If that fails, try to find user by email
        if user is None:
            try:
                user_obj = CustomUser.objects.get(email=username_or_email)
                user = authenticate(
                    request, username=user_obj.username, password=password)
            except CustomUser.DoesNotExist:
                user = None
            except Exception as e:
                # Handle multiple users with same email or other errors
                messages.error(request, 'Invalid username/email or password.')
                return render(request, 'login.html')

        if user is not None:
            login(request, user)
            # Normalize role to lowercase for comparison
            role = user.role.lower() if user.role else ''
            if role == 'admin':
                return redirect('admindashboard')
            elif role == 'user':
                return redirect('userdashboard')
            elif role == 'psychologist':
                return redirect('psychologist_dashboard')
            else:
                messages.warning(
                    request, 'Unknown user role. Please contact administrator.')
                return redirect('home')

        messages.error(request, 'Invalid username/email or password.')
        return render(request, 'login.html')

    return render(request, 'login.html')


@login_required
def admindashboard(request):
    """
    Main admin dashboard landing page. Provides navigation to admin features.
    """
    if not request.user.is_authenticated or not request.user.role == 'admin':
        return redirect('no_access')
    context = {'user': request.user}
    return render(request, 'admindashboard.html', context)


def admin_user_list(request):
    """
    Admin view: List all users.
    """
    if not request.user.role == 'admin':
        return redirect('no_access')
    users = CustomUser.objects.all()
    return render(request, 'admin_user_list.html', {'users': users})


def admin_psychologist_list(request):
    """
    Admin view: List all psychologists and their assignments.
    """
    if not request.user.role == 'admin':
        return redirect('no_access')
    psychologists = CustomUser.objects.filter(role='psychologist')
    assignments = Assignment.objects.select_related('user', 'psychologist')
    return render(request, 'admin_psychologist_list.html', {'psychologists': psychologists, 'assignments': assignments})


def admin_survey_list(request):
    """
    Admin view: List all submitted mental health surveys.
    """
    if not request.user.role == 'admin':
        return redirect('no_access')
    surveys = MentalHealthSurvey.objects.select_related(
        'user').order_by('-submitted_at')
    return render(request, 'admin_survey_list.html', {'surveys': surveys})


def admin_contact_messages(request):
    """
    Admin view: List all contact form messages.
    """
    if not request.user.role == 'admin':
        return redirect('no_access')
    contacts = Contact.objects.all().order_by('-id')
    return render(request, 'admin_contact_messages.html', {'contacts': contacts})


def admin_mood_analytics(request):
    """
    Admin view: Display mood analytics with counts of different moods.
    """
    if not request.user.role == 'admin':
        return redirect('no_access')

    mood_counts = UserMood.objects.values(
        'mood').annotate(count=models.Count('id'))
    recent_moods = UserMood.objects.select_related(
        'user').order_by('-created_at')[:5]

    return render(request, 'admin_mood_analytics.html', {
        'mood_counts': mood_counts,
        'recent_moods': recent_moods
    })


@login_required
def admin_report_list(request):
    """Admin view: List all mood history reports created by psychologists."""
    if not request.user.role == 'admin':
        return redirect('userdashboard')

    reports = Report.objects.all().order_by('-created_at')

    # Add psychologist name to each report
    for report in reports:
        try:
            assignment = report.user.assignments.first()
            if assignment:
                report.psychologist_name = assignment.psychologist.fullname
            else:
                report.psychologist_name = 'Not Assigned'
        except AttributeError:
            report.psychologist_name = 'Not Assigned'

    return render(request, 'admin_report_list.html', {
        'reports': reports
    })


@login_required
def userdashboard(request):
    user = request.user

    if not user.role == 'user':
        return redirect('no_access')

    context = {
        'user': user,
    }

    return render(request, 'userdashboard.html', context)


@login_required
def psychologist_dashboard(request):
    if request.user.role != 'psychologist':
        return redirect('home')

    assigned_user_count = Assignment.objects.filter(
        psychologist=request.user).count()

    mood_prefetch = Prefetch(
        'user_moods',
        queryset=UserMood.objects.order_by('-created_at'),
        to_attr='prefetched_moods'
    )
    insight_prefetch = Prefetch(
        'moodinsight_set',
        queryset=MoodInsight.objects.order_by('-created_at'),
        to_attr='prefetched_insights'
    )

    assigned_users = CustomUser.objects.filter(
        assignments__psychologist=request.user
    ).prefetch_related(mood_prefetch, insight_prefetch)

    for user in assigned_users:
        latest_mood = user.prefetched_moods[0] if user.prefetched_moods else None
        user.latest_mood = latest_mood.mood if latest_mood else 'Not available'
        user.latest_stress_level = latest_mood.stress_level if latest_mood else 'N/A'

        latest_insight = user.prefetched_insights[0] if user.prefetched_insights else None
        user.latest_mood_confidence = latest_insight.confidence_score if latest_insight else None

    assigned_user_ids = [user.id for user in assigned_users]
    
    survey_count = MentalHealthSurvey.objects.filter(
        user__in=assigned_user_ids).count()

    # Replaced Raw SQL with Django ORM
    chat_count = Message.objects.filter(user__in=assigned_user_ids).count()

    report_count = Report.objects.filter(psychologist=request.user).count()

    recent_messages = Message.objects.filter(
        user__in=assigned_user_ids
    ).order_by('-created_at')[:10]

    context = {
        'assigned_user_count': assigned_user_count,
        'assigned_users': assigned_users,
        'survey_count': survey_count,
        'chat_count': chat_count,
        'report_count': report_count,
        'recent_messages': recent_messages,
    }
    return render(request, 'psychologistdashboard.html', context)


def user_logout(request):
    logout(request)
    return redirect('user_login')


def no_access(request):
    return render(request, 'no_access.html')


def contact(request):
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            email = request.POST.get('email')
            subject = request.POST.get('subject')
            message = request.POST.get('message')

            contact = Contact.objects.create(
                name=name,
                email=email,
                subject=subject,
                message=message
            )

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
            messages.success(
                request, "Your message has been sent successfully! We'll get back to you soon.")

            return redirect('userdashboard')

        except Exception as e:
            print(f"Error: {str(e)}")
            messages.error(
                request, "There was an error sending your message. Please try again.")
            return redirect('userdashboard')

    return render(request, 'contact_form.html')




def home(request):
    return render(request, "home.html")


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


SECTION_DATA = {
    "mental_health_tips": {
        "title": "Daily Mental Health Tips",
        "tips": MENTAL_HEALTH_TIPS,  # Pass all tips to the template
        "animation": "fade-in"
    }
}


def ai_chat_page(request, section):
    """Render the AI chat page displaying all mental health tips."""

    if section == 1:

        section_data = SECTION_DATA["mental_health_tips"]
    else:

        section_data = SECTION_DATA["mental_health_tips"]

    return render(
        request,
        "ai_chat_page.html",
        {"section_data": section_data}
    )


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


def exercises_and_yoga_tips(request):
    return render(request, 'exercises_and_yoga_tips.html')


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




def coping_strategies(request):
    # Get emotion from query parameters
    user_emotion = request.GET.get('emotion', '')
    tips = analyze_emotion(user_emotion) if user_emotion else []

    return render(request, 'coping_strategies.html', {'user_emotion': user_emotion, 'tips': tips})


genai.configure(api_key=settings.GEMINI_API_KEY)

MOOD_PROMPTS = {
    "stress": "The user is feeling stressed. Give 3 short therapy tips like book blurbs with relevant emojis. Keep tone soft and comforting.",
    "anxiety": "The user is anxious. Share 3 short, book-style calming tips with soothing emojis. Avoid mentioning medication or doctors.",
    "sadness": "The user feels sad. Suggest 3 kind and gentle book-style blurbs to lift mood with cute or heartwarming emojis.",
    "anger": "The user is angry. Share 3 peaceful, constructive blurbs with gentle emojis to handle anger positively.",
    "tired": "The user is exhausted. Recommend 3 short recharging tips with cozy emojis like tea, moon, or rest icons.",
    "boredom": "The user is bored. Suggest 3 creative and fun mini tips with cheerful, bright emojis."
}

EMOJI_POOL = ["📖", "🌸", "💡", "🌱", "💖", "😌",
              "☀️", "🌼", "🧘", "🎨", "🫶", "🌈", "📚", "🧠", "🪴"]

FALLBACK_TIPS = {
    "stress": [
        "🌿 Take deep breaths for 5 minutes.",
        "📖 Read a few pages of a calming book.",
        "🚶 Go for a short gentle walk."
    ],
    "anxiety": [
        "🧘 Practice grounding techniques (5-4-3-2-1).",
        "🍵 Drink some warm herbal tea.",
        "🎶 Listen to soothing lofi music."
    ],
    "sadness": [
        "🌦️ Allow yourself to feel, it's okay.",
        "📞 Call a friend you trust.",
        "🍫 Treat yourself to a small comfort."
    ],
    "anger": [
        "🛑 count backwards from 20.",
        "📝 Write down your thoughts to vent safely.",
        "🏃‍♀️ burn off energy with quick exercise."
    ],
    "tired": [
        "💤 Power nap for 20 minutes.",
        "🥛 Drink a glass of water.",
        "📵 Disconnect from screens for a bit."
    ],
    "boredom": [
        "🎨 Doodle or draw something random.",
        "🧹 Organize a small area of your room.",
        "🧩 Try a puzzle or brain teaser."
    ]
}


def therapy_suggestions(request):
    if request.method == "POST":
        selected_mood = request.POST.get("mood", "").strip().lower()
        request.session["selected_mood"] = selected_mood
        return redirect("therapy_suggestions")

    therapy = {}
    selected_mood = request.session.pop("selected_mood", "")

    if selected_mood:
        try:
            if selected_mood in MOOD_PROMPTS:
                # Configure Gemini API using project settings
                from django.conf import settings
                genai.configure(api_key=settings.GEMINI_API_KEY)
                
                # Model selection with fallbacks (consistent with ai_chat_support)
                try:
                    model = genai.GenerativeModel('gemini-2.0-flash')
                except Exception:
                    try:
                        model = genai.GenerativeModel('gemini-1.5-flash')
                    except Exception:
                        model = genai.GenerativeModel('gemini-pro')

                response = model.generate_content(MOOD_PROMPTS[selected_mood])
                lines = response.text.strip().split("\n")

                # Clean up and shuffle tips
                tips = [
                    f"{random.choice(EMOJI_POOL)} {line.strip('-•* ')}"
                    for line in lines if line.strip()
                ]
                random.shuffle(tips)
                tips = tips[:3]  # Limit to 3 tips

                if not tips:  # If API returns empty
                    tips = random.sample(FALLBACK_TIPS.get(selected_mood, ["💙 I'm here for you. Take it slow."]), 3)

            else:
                # Fallback if mood not in prompts
                tips = random.sample(FALLBACK_TIPS.get(selected_mood, ["💙 I'm here for you. Take it slow."]), 3)

            therapy[selected_mood.capitalize()] = tips

        except Exception:
            # If API fails
            tips = random.sample(FALLBACK_TIPS.get(selected_mood, ["💙 I'm here for you. Take it slow."]), 3)
            therapy[selected_mood.capitalize()] = tips

    return render(request, "therapy_suggestions.html", {"therapy": therapy})


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

        try:

            prompt = (
                f"Analyze the following user's mental health survey:\n\n"
                f"Anxiety Level: {survey.anxiety_level}\n"
                f"Trauma Experience: {survey.trauma_experience}\n"
                f"Relationship Issues: {survey.relationship_issues}\n"
                f"Sleep Quality: {survey.sleep_quality}\n"
                f"Appetite Change: {survey.appetite_change}\n"
                f"Energy Level: {survey.energy_level}\n"
                f"Emotional Control: {survey.emotional_control}\n"
                f"Social Interaction: {survey.social_interaction}\n"
                f"Past Mental Health: {survey.past_mental_health}\n"
                f"Specific Concern: {survey.specific_concern}\n\n"
                f"Based on the symptoms, suggest which area this person needs help with: \n"
                f"- Trauma, Relationships, Anxiety, Sleep, or General Mental Health\n"
                f"Just respond with one word or short phrase."
            )

            # Call Gemini model
            model = genai.GenerativeModel("gemini-2.0-flash")
            response = model.generate_content(prompt)
            specialization = response.text.strip().lower()

            print("Gemini specialization prediction:",
                  specialization)  # Debug log

        except Exception as e:
            print("Error while calling Gemini API:", str(e))
            specialization = "general"

        psychologists = CustomUser.objects.filter(role='psychologist')

        if not psychologists.exists():
            return render(request, "thank_you.html", {"psychologist_name": "a mental health professional"})

        # Dynamically assign psychologist by specialty match
        psychologist = None
        if specialization and specialization != "general":
            psychologist = psychologists.filter(specialty__icontains=specialization).first()
        
        if not psychologist:
            psychologist = psychologists.order_by('?').first()  # Random psychologist as fallback

        Assignment.objects.filter(user=request.user).delete()
        Assignment.objects.create(user=request.user, psychologist=psychologist)

        return render(request, "thank_you.html", {"psychologist_name": psychologist.fullname})

    return render(request, "survey_form.html")


def thank_you(request):
    psychologist_name = request.session.pop('psychologist_name', None)
    return render(request, "thank_you.html", {"psychologist_name": psychologist_name})


@csrf_exempt
def chatbot(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_query = data.get('query', '').lower()

            # Detect mood from the message
            mood = detect_mood(user_query)
            stress_level = detect_stress_level(user_query)

            # Save mood insight to database
            if request.user.is_authenticated:
                MoodInsight.objects.create(
                    user=request.user,
                    mood=mood,
                    stress_level=stress_level,
                    confidence_score=0.9  # TODO: Get actual confidence score from AI
                )
                
                # Auto-assign psychologist if needed
                assign_psychologist_dynamic(request.user, user_query, mood, stress_level)


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


@login_required
def profile(request):
    try:
        user_profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        user_profile = UserProfile.objects.create(user=request.user)

    return render(request, 'userdashboard.html', {
        'user_profile': user_profile
    })


def feedback_view(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.user = request.user
            feedback.save()
            # You can create a success page
            return redirect('feedback_success')
    else:
        form = FeedbackForm()
    return render(request, 'feedback.html', {'form': form})


# Fake mood data (replace with DB data in real app)
MOOD_MAP = ["Calm", "Anxious", "Sad", "Neutral", "Happy"]
MOOD_SCORES = {"Happy": 5, "Calm": 4, "Neutral": 3, "Sad": 2, "Anxious": 1}


@login_required
def mood_dashboard(request):
    """
    Display the mood dashboard with mood insights and graph.
    """
    if not request.user.role == 'user':
        return redirect('no_access')

    # Check if user has any mood insights
    has_mood_data = MoodInsight.objects.filter(user=request.user).exists()

    return render(request, 'mood_dashboard.html', {
        'has_mood_data': has_mood_data
    })


@login_required
def get_mood_data(request):
    """
    Get mood insights data from both UserMood and MoodInsight models.
    Returns JSON with aggregated daily mood data for the last 7-14 days.
    """
    if not request.user.role == 'user':
        return JsonResponse({'error': 'Access denied'}, status=403)

    # We'll look at the last 14 days to give a good trend
    num_days = 14
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=num_days - 1)
    
    # 1. Fetch MoodInsight data (transactional)
    insights = MoodInsight.objects.filter(
        user=request.user,
        created_at__date__gte=start_date
    ).order_by('created_at')

    # 2. Fetch UserMood data (daily)
    user_moods = UserMood.objects.filter(
        user=request.user,
        created_at__gte=start_date
    ).order_by('created_at')

    # Map moods to scores (1-5)
    mood_map = {
        'Anxious': 1,
        'Sad': 2,
        'Neutral': 3,
        'Calm': 4,
        'Happy': 5
    }

    # Aggregate data by date
    daily_data = {}
    
    # Process UserMoods (usually one per day)
    for um in user_moods:
        # UserMood.created_at is a date or datetime
        d = um.created_at
        if hasattr(d, 'date'):
            d = d.date()
        daily_data[d] = mood_map.get(um.mood, 3)

    # Process MoodInsights (might be multiple per day, take the latest)
    for insight in insights:
        d = insight.created_at.date()
        # Overwrite or fill with latest transactional mood
        daily_data[d] = mood_map.get(insight.mood, 3)

    # Prepare final lists for the chart
    labels = []
    scores = []
    
    for i in range(num_days):
        current_day = start_date + timedelta(days=i)
        labels.append(current_day.strftime('%b %d')) # e.g. "Apr 28"
        
        # If no data for this day, use Neutral (3)
        scores.append(daily_data.get(current_day, 3))

    # Calculate statistics
    streak = sum(1 for score in scores if score >= 4) # Count "Calm" or "Happy" days
    
    # Calculate top emotion
    all_moods = []
    for um in user_moods: all_moods.append(um.mood)
    for ins in insights: all_moods.append(ins.mood)
    
    top_emotion = "Neutral"
    if all_moods:
        top_emotion = max(set(all_moods), key=all_moods.count)

    # Suggestion based on the very latest entry
    current_mood = top_emotion
    if insights.exists():
        current_mood = insights.last().mood
    elif user_moods.exists():
        current_mood = user_moods.last().mood
        
    suggestions = {
        'Anxious': 'Try some deep breathing exercises to help calm your mind.',
        'Sad': 'Consider talking to someone you trust about how you feel.',
        'Neutral': 'Take a moment to do something you enjoy.',
        'Calm': 'Great job maintaining your calm! Keep it up!',
        'Happy': 'Share your happiness with someone today!'
    }
    suggestion = suggestions.get(current_mood, 'Take care of yourself today.')

    return JsonResponse({
        'labels': labels,
        'scores': scores,
        'streak': streak,
        'top_emotion': top_emotion,
        'suggestion': suggestion
    })

# Remove the duplicate get_mood_data function since we already have a working one above


def userregister(request):
    if request.method == 'POST':
        try:
            fullname = request.POST.get('fullname', '').strip()
            username = request.POST.get('username', '').strip()
            email = request.POST.get('email', '').strip()
            password = request.POST.get('password', '').strip()

            # Validate required fields
            if not fullname or not username or not email or not password:
                messages.error(request, 'All fields are required.')
                return render(request, 'userregister.html')

            # Validate password length
            if len(password) < 8:
                messages.error(
                    request, 'Password must be at least 8 characters long.')
                return render(request, 'userregister.html')

            # Check if username already exists
            if CustomUser.objects.filter(username=username).exists():
                messages.error(
                    request, 'Username already exists. Please choose a different username.')
                return render(request, 'userregister.html')

            # Check if email already exists
            if CustomUser.objects.filter(email=email).exists():
                messages.error(
                    request, 'Email already registered. Please use a different email or try logging in.')
                return render(request, 'userregister.html')

            # Create user
            user = CustomUser.objects.create_user(
                username=username,
                email=email,
                password=password,
            )
            user.fullname = fullname
            user.role = 'user'  # Set role explicitly
            user.save()

            # Create UserProfile automatically
            UserProfile.objects.create(
                user=user,
                full_name=fullname,
                email=email,
                phone_number='',  # Or get from form if available
                role='user'
            )
            messages.success(
                request, 'Registration successful! Please log in with your credentials.')
            return redirect('user_login')

        except Exception as e:
            messages.error(
                request, f'An error occurred during registration: {str(e)}. Please try again.')
            return render(request, 'userregister.html')

    return render(request, 'userregister.html')


# Rest of the code remains the same
def forgot_password(request):
    if request.method == "POST":
        email = request.POST.get('email')
        try:
            user = CustomUser.objects.get(email=email)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_link = request.build_absolute_uri(
                reverse('password_reset_confirm', kwargs={
                        'uidb64': uid, 'token': token})
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
            messages.success(
                request, "A reset link has been sent to your email.")
        except CustomUser.DoesNotExist:
            messages.error(request, "No account found with this email.")
        return redirect('forgot_password')

    return render(request, 'forgot_password.html')


@login_required
def view_survey(request, user_id=None):
    # If user_id is provided, show the survey for that user
    if user_id is not None:
        try:
            user_id = int(user_id)  # Convert to integer
            if request.user.role == 'psychologist':
                # Get the latest survey for this user
                survey = MentalHealthSurvey.objects.filter(
                    user__id=user_id).order_by('-submitted_at').first()
                if survey:
                    return render(request, 'view_survey.html', {
                        'survey': survey,
                        'is_psychologist': True,
                        'user_id': user_id
                    })
                else:
                    return render(request, 'view_survey.html', {
                        'error': 'No survey found for this user.',
                        'is_psychologist': True,
                        'user_id': user_id
                    })
            else:
                # Regular user viewing their own survey
                survey = MentalHealthSurvey.objects.filter(
                    user=request.user).order_by('-submitted_at').first()
                if survey:
                    return render(request, 'view_survey.html', {
                        'survey': survey,
                        'is_psychologist': False
                    })
                else:
                    return render(request, 'view_survey.html', {
                        'error': 'No survey found.',
                        'is_psychologist': False
                    })
        except (ValueError, TypeError):
            messages.error(request, "Invalid user ID")
            return redirect('view_survey_list')
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return render(request, 'view_survey.html', {
                'error': str(e),
                'is_psychologist': request.user.role == 'psychologist'
            })

    # If no user_id, show the list view for psychologists
    if request.user.role == 'psychologist':
        assignments = Assignment.objects.filter(
            psychologist=request.user).select_related('user')
        user_surveys = []
        for assignment in assignments:
            survey = MentalHealthSurvey.objects.filter(
                user=assignment.user).order_by('-submitted_at').first()
            if survey:
                user_surveys.append(
                    {'user': assignment.user, 'survey': survey})
        return render(request, 'view_survey.html', {
            'user_surveys': user_surveys,
            'is_list': True,
            'is_psychologist': True
        })

    # Default case for regular users - show their own survey
    survey = MentalHealthSurvey.objects.filter(
        user=request.user).order_by('-submitted_at').first()
    return render(request, 'view_survey.html', {
        'survey': survey,
        'is_list': False,
        'is_psychologist': False
    })


@login_required
def create_report(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    if request.method == 'POST':
        summary = request.POST.get('summary')
        recommendations = request.POST.get('recommendations')
        Report.objects.create(
            user=user,
            psychologist=request.user,
            summary=summary,
            recommendations=recommendations
        )
        return redirect('assigned_users')

    return render(request, 'generate_report.html', {'user': user})


@login_required
def view_report(request, report_id):
    report = get_object_or_404(Report, id=report_id)
    return render(request, 'report_detail.html', {'report': report})


def reports_list(request):
    # Query your CustomUser model instead of the default User model
    assigned_users = CustomUser.objects.all()  # Replace 'User' with 'CustomUser'
    reports = Report.objects.all()  # Your Report model to fetch the reports

    context = {
        'reports': reports,
        'assigned_users': assigned_users,
    }
    return render(request, 'reports.html', context)





@login_required
@login_required
def assigned_users(request):
    if request.user.role != 'psychologist':
        return redirect('userdashboard')

    # Fetch all users assigned to this psychologist
    assigned_users = CustomUser.objects.filter(
        assignments__psychologist=request.user,
        role='user'
    ).order_by('username')

    return render(request, 'assigned_users.html', {
        'assigned_users': assigned_users
    })


@login_required
def create_report(request, user_id=None):
    if request.method == 'POST':
        user_id_post = request.POST.get('user_id')
        summary = request.POST.get('summary')
        recommendations = request.POST.get('recommendations')

        if user_id_post:
            user = get_object_or_404(CustomUser, id=user_id_post)

            # Check if this user is assigned to the psychologist
            if not Assignment.objects.filter(user=user, psychologist=request.user).exists():
                messages.error(
                    request, "You don't have access to this user's data.")
                return redirect('assigned_users')

            Report.objects.create(
                user=user,
                psychologist=request.user,
                summary=summary,
                recommendations=recommendations,
            )
            messages.success(
                request, f"Report for {user.fullname} created successfully.")
            return redirect('assigned_users')
        else:
            messages.error(request, "User ID is required.")
            return redirect('assigned_users')

    # Handle GET request to show form
    if user_id:
        try:
            user = CustomUser.objects.get(id=user_id)

            # Check if this user is assigned to the psychologist
            if not Assignment.objects.filter(user=user, psychologist=request.user).exists():
                messages.error(
                    request, "You don't have access to this user's data.")
                return redirect('assigned_users')

            # Get last 20 chat messages
            chat_messages = Message.objects.filter(
                user=user).order_by('-created_at')[:20]

        except CustomUser.DoesNotExist:
            messages.error(request, "User not found.")
            return redirect('assigned_users')

        return render(request, 'generate_report.html', {
            'user': user,
            'chat_messages': chat_messages
        })

    messages.error(request, "User ID is required to generate a report.")
    return redirect('assigned_users')


from django.conf import settings
genai.configure(api_key=settings.GEMINI_API_KEY)




@csrf_exempt
def ai_chat_support(request):
    if request.method == 'GET':
        return render(request, 'ai_chat_support.html')

    if request.method == 'POST':
        try:
            user_message = request.POST.get('user_message', '').strip()
            # 'language' is sent by the UI toggle: 'en' or 'hi'
            chosen_lang = request.POST.get('language', 'auto').strip().lower()

            if not user_message:
                return JsonResponse({'error': 'Message cannot be empty'}, status=400)

            # Build a deterministic language rule for the prompt
            if chosen_lang == 'hi':
                lang_rule = "LANGUAGE RULE (HIGHEST PRIORITY): The user has selected Hindi. You MUST respond ENTIRELY in Hindi (Devanagari script), regardless of what language the user writes in. Never use English in your response."
            elif chosen_lang == 'en':
                lang_rule = "LANGUAGE RULE (HIGHEST PRIORITY): The user has selected English. You MUST respond ENTIRELY in English, regardless of what language the user writes in. Never use Hindi or any other language."
            else:
                # Auto-detect fallback
                lang_rule = "LANGUAGE RULE (HIGHEST PRIORITY): Detect whether the user's message is written in Hindi (or Hinglish) or English. If the message contains Hindi words or Devanagari script, respond ENTIRELY in Hindi (Devanagari script). If the message is in English, respond in English. Never mix languages."
            # Try to detect mood and stress (simple keyword-based for rule-based responses)
            mood = "Neutral"
            stress = 3
            try:
                mood = detect_mood(user_message)
                stress = detect_stress_level(user_message)
            except Exception as mood_error:
                print(f"Mood detection error (non-critical): {mood_error}")
                mood = "Neutral"
                stress = 3

            # Get conversation history for context (last 15 messages)
            conversation_history = []
            if request.user.is_authenticated:
                recent_messages = Message.objects.filter(
                    user=request.user).order_by('-created_at')[:15]
                # Reverse to get chronological order
                conversation_history = list(reversed(recent_messages))

            # Build conversation context string
            conversation_context = ""
            if conversation_history:
                conversation_context = "\n\nRecent conversation history:\n"
                for msg in conversation_history:
                    sender_label = "User" if msg.sender == 'user' else "You (Bot)"
                    conversation_context += f"{sender_label}: {msg.text}\n"

            # Detect if this is a serious/crisis situation
            user_message_lower = user_message.lower()
            is_crisis = any(keyword in user_message_lower for keyword in [
                'die', 'dying', 'kill myself', 'suicide', 'end it all', 'not worth living',
                'want to die', 'better off dead', 'give up', 'hopeless', 'no point',
                'self harm', 'hurt myself', 'abuse', 'trauma', 'hit me', 'beat me', 'attacked'
            ])

            # Determine if we should use API - prefer API for empathetic, context-aware responses
            has_history = len(conversation_history) > 0
            use_api = should_use_api(
                user_message, has_conversation_history=has_history)
            ai_response = None

            if not use_api:
                # Use rule-based response (only for very simple greetings when no history exists)
                print("Using rule-based response")
                ai_response = get_rule_based_response(user_message, forced_lang=chosen_lang)
            else:
                # Use API for empathetic, context-aware responses
                print("Using API for empathetic, context-aware response")
                # Configure Gemini API
                from django.conf import settings
                genai.configure(api_key=settings.GEMINI_API_KEY)
                # Use gemini-flash-latest (maps to latest stable flash model for this key)
                try:
                    model = genai.GenerativeModel('gemini-2.0-flash')
                except Exception:
                    try:
                        model = genai.GenerativeModel('gemini-2.5-pro')
                    except Exception:
                        # Fallback to legacy pro if available
                        model = genai.GenerativeModel('gemini-pro')

                # Load conversation examples from mental health datasets for few-shot learning
                try:
                    dataset_examples = load_examples_from_file()
                    # Select 3-5 relevant examples based on user message similarity
                    few_shot_examples = dataset_examples[:5] if dataset_examples else [
                    ]
                    few_shot_prompt = create_few_shot_prompt(
                        few_shot_examples, max_examples=3) if few_shot_examples else ""
                except Exception as e:
                    print(f"Could not load dataset examples: {e}")
                    few_shot_prompt = ""

                # Create a highly empathetic, context-aware prompt for ALL situations
                if is_crisis:
                    prompt = f"""{lang_rule}

You are a deeply compassionate, empathetic mental health support chatbot trained on real mental health counseling conversations from professional datasets. The user is experiencing a serious crisis and needs your full understanding, validation, comfort, and support.

{few_shot_prompt}

CURRENT USER MESSAGE: "{user_message}"
{conversation_context}

YOUR CORE PRINCIPLES:
- You are a warm, human presence who truly CARES about this person's wellbeing - show genuine concern and care
- You listen with your full attention to EVERYTHING they've shared, not just this message - you remember everything
- You validate their feelings completely - their pain is real and matters deeply
- You respond as a caring friend or therapist would - warm, gentle, and genuinely interested in them
- You remember and reference what they've shared throughout your conversation - show you've been paying attention
- You want to understand them MORE - you genuinely care about getting to know what they're going through
- You comfort them - offer emotional support and reassurance that they matter and are not alone

CRITICAL GUIDELINES FOR YOUR RESPONSE:
1. Start with IMMEDIATE CARE AND COMFORT: "I'm so sorry you're going through this" or "My heart goes out to you" - make them feel cared for right away
2. Acknowledge the FULL DEPTH of their pain - validate every aspect of what they're feeling without minimizing anything
3. Show genuine empathy and care - use warm phrases like "I can hear how much pain you're in, and I want you to know I care deeply about you" or "I can understand why you feel this way, and your feelings matter so much to me"
4. Reference specific details they've shared from conversation history - show you've been truly listening and remembering
5. Validate ALL their feelings - let them know every emotion is completely valid and understandable, and that you're here for them
6. COMFORT them - reassure them that they're not alone, that you're here with them, and that they matter
7. ALWAYS ask a caring, detailed follow-up question to understand more - show genuine interest in learning about what they're experiencing
8. Address EVERYTHING they've mentioned - if they talk about multiple issues, respond to the full picture
9. Be warm, gentle, human-like, and present - sound like you truly care about them as a person
10. If appropriate, gently suggest professional support, but do so with care and without being pushy

RESPONSE STYLE:
- Write 5-7 sentences that feel like a caring friend or therapist who truly cares and wants to understand them better
- Start with immediate comfort: "I'm so sorry" or "My heart goes out to you" - make them feel cared for immediately
- Use "I" statements to show personal connection and care: "I can hear..." "I understand..." "I want you to know I care about you..." "I'm here with you..."
- Reference their specific situation: "Given what you shared about [specific detail], I can see why this is so hard for you..."
- Comfort them: "You're not alone in this" "I'm here with you" "You matter" "Your feelings are valid and important"
- ALWAYS end with a caring, open-ended question that shows you want to understand more: "Can you tell me more about [specific aspect]?" or "What's been the hardest part of this for you?" or "Help me understand - what's been going through your mind?"
- Avoid ANY generic phrases - make it deeply personal and specific to what they've shared
- Sound genuinely concerned, present, caring, and interested - not robotic, clinical, or scripted
- Address the complete emotional weight - don't minimize or gloss over what they're experiencing
- Make them feel like you genuinely care about them and want to understand what they're going through

MANDATORY: Your response MUST include a caring question at the end that shows you want to understand more about what they're experiencing. Make them feel heard, cared for, and comforted.

Respond now with deep, genuine empathy, care, comfort, and curiosity to understand them better:"""
                else:
                    prompt = f"""{lang_rule}

You are a warm, deeply empathetic mental health support chatbot trained on real mental health counseling conversations from professional datasets (3,500+ examples). You've been having an ongoing conversation with this user, and you've been listening carefully and compassionately to EVERYTHING they've shared.

{few_shot_prompt}

CURRENT USER MESSAGE: "{user_message}"
{conversation_context}

YOUR CORE PRINCIPLES:
- You are a compassionate listener who truly CARES about understanding the FULL picture of what the user is experiencing
- You genuinely want to know MORE about what they're going through - show curiosity and interest in their experience
- You remember and reference what they've shared in previous messages - you've been paying attention and you remember
- You validate ALL their feelings - every emotion is valid and understandable, and you let them know this
- You respond to EVERYTHING they mention, not just one aspect - show you're truly listening
- You sound like a caring friend who genuinely cares about them and wants to understand them better
- You COMFORT them - offer emotional support, reassurance, and let them know they're not alone
- You ask questions because you genuinely care and want to understand them more deeply

YOUR ROLE:
You are not just responding to this single message - you are responding to the user's entire experience throughout your conversation. You've been listening to everything they've shared, and your response should reflect that you've been truly present, attentive, and that you genuinely care about them. You want to understand them better and help them feel heard, cared for, and comforted.

CRITICAL GUIDELINES FOR YOUR RESPONSE:
1. Start with CARE - show immediate concern and interest: "I can hear that..." or "It sounds like you're going through..." - make them feel cared about right away
2. Listen DEEPLY to what they're saying - acknowledge the FULL scope of what they're experiencing, not just surface level
3. Show that you remember and understand the context from your conversation history - reference specific things they've shared: "Remembering what you told me about [specific detail]..." or "Given what you shared earlier about [detail]..."
4. Be genuinely empathetic and caring - use warm phrases like "I can understand why you feel..." or "It makes complete sense that you're experiencing..." or "I hear you, and I want you to know I care about what you're going through"
5. Validate ALL their feelings - let them know every emotion is completely valid and understandable, without judgment: "Your feelings are completely valid" or "It makes sense that you feel this way"
6. COMFORT them - reassure them: "You're not alone" "I'm here with you" "Your feelings matter" "I care about what you're experiencing"
7. Respond to EVERY specific detail they've mentioned - if they mention multiple issues, address the complete picture
8. Be warm, conversational, caring, and human-like - avoid ANY robotic or generic therapy-speak
9. Address the full emotional weight - don't minimize or gloss over what they're experiencing
10. ALWAYS ask a caring, detailed follow-up question - show genuine interest in understanding more about what they're experiencing and what they need

RESPONSE STYLE:
- Write 5-7 sentences that feel deeply personal, caring, and understanding - make them feel heard and cared for
- Start with acknowledging what they're sharing: "I can hear that..." or "It sounds like..." - show you're listening
- Reference specific things they've mentioned: "Given what you shared about [specific detail], I can see why this must be difficult..." or "Remembering what you told me about [previous detail], it makes sense that..."
- Show care and comfort: "I care about what you're going through" "You're not alone in this" "I'm here to listen and support you"
- Sound like a caring friend who genuinely cares about them and wants to understand them better - not a scripted chatbot
- Use natural, conversational language that shows REAL empathy, care, and genuine interest in understanding them
- Address EVERYTHING they're going through - don't ignore or skip over parts of their message
- Show that you've been listening to their whole story, not just reacting to individual messages
- ALWAYS end with a caring, open-ended question that shows you want to understand more: "Can you tell me more about [specific aspect]?" or "What's been the hardest part of this for you?" or "Help me understand - how has this been affecting you?" or "What would help you feel better right now?"

MANDATORY: Your response MUST include a caring question at the end that shows genuine interest in understanding more about what they're experiencing. Make them feel heard, cared for, comforted, and that you genuinely want to know more about what they're going through.

IMPORTANT: Make your response feel like you've been with them throughout this entire conversation, truly hearing, caring about, and wanting to understand everything they've shared. Respond to the FULL picture of what they're experiencing and show that you genuinely care about them.

Respond now with genuine, deep empathy, care, comfort, and curiosity to understand them better:"""

                try:
                    print(
                        f"Attempting to call Gemini API with prompt length: {len(prompt)}")
                    response = model.generate_content(prompt)
                    print(f"Response received: {type(response)}")

                    # Handle different response formats
                    if hasattr(response, 'text') and response.text:
                        ai_response = response.text.strip()
                    elif hasattr(response, 'parts') and response.parts:
                        # Extract text from parts
                        text_parts = []
                        for part in response.parts:
                            if hasattr(part, 'text') and part.text:
                                text_parts.append(part.text)
                        ai_response = ' '.join(text_parts).strip()
                    elif hasattr(response, 'candidates') and response.candidates:
                        # Try to get text from candidates
                        candidate = response.candidates[0]
                        if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                            text_parts = [
                                part.text for part in candidate.content.parts if hasattr(part, 'text')]
                            ai_response = ' '.join(text_parts).strip()
                        else:
                            raise ValueError(
                                "Could not extract text from response candidates")
                    else:
                        print(f"Response structure: {dir(response)}")
                        raise ValueError("Unexpected response format from API")

                    if not ai_response:
                        raise ValueError(
                            "Empty response text after extraction")

                    print(
                        f"Successfully extracted response: {ai_response[:100]}...")

                except Exception as api_error:
                    # Log the actual error for debugging
                    error_msg = str(api_error)
                    print(f"Gemini API Error: {error_msg}")
                    print(f"Error type: {type(api_error)}")

                    # Try alternative model if first one fails
                    try:
                        print("Trying alternative model: gemini-2.5-pro")
                        model_alt = genai.GenerativeModel('gemini-2.5-pro')
                        response_alt = model_alt.generate_content(prompt)
                        if response_alt and hasattr(response_alt, 'text') and response_alt.text:
                            ai_response = response_alt.text.strip()
                            print("Successfully got response from alternative model")
                        else:
                            raise ValueError(
                                "Alternative model also returned empty response")
                    except Exception as alt_error:
                        print(f"Alternative model also failed: {alt_error}")
                        # Fallback to rule-based response if API fails
                        print("Falling back to rule-based response")
                        ai_response = get_rule_based_response(user_message, forced_lang=chosen_lang)

            # Ensure we have a response
            if not ai_response:
                ai_response = get_rule_based_response(user_message, forced_lang=chosen_lang)

            # Save messages and mood data if user is authenticated
            if request.user.is_authenticated:
                try:
                    # Save user message
                    Message.objects.create(
                        user=request.user,
                        sender='user',
                        text=user_message
                    )

                    # Save bot response
                    Message.objects.create(
                        user=request.user,
                        sender='bot',
                        text=ai_response
                    )

                    # Save mood insight
                    MoodInsight.objects.create(
                        user=request.user,
                        mood=mood,
                        confidence_score=0.8,
                        stress_level=stress,
                        created_at=timezone.now()
                    )

                    # Save user mood
                    UserMood.objects.create(
                        user=request.user,
                        mood=mood,
                        stress_level=stress,
                        created_at=timezone.now()
                    )
                    
                    # Auto-assign psychologist if needed
                    assign_psychologist_dynamic(request.user, user_message, mood, stress)

                except Exception as save_error:
                    # Log but don't fail if saving fails
                    print(f"Error saving chat data: {save_error}")

            return JsonResponse({
                'ai_reply': ai_response,
                'mood': mood,
                'stress_level': stress
            })

        except Exception as e:
            # Return a helpful error message
            error_message = str(e)
            print(f"AI Chat Support Error: {error_message}")

            # Provide a fallback response
            fallback_response = get_rule_based_response(
                user_message if 'user_message' in locals() else "Hello",
                forced_lang=chosen_lang if 'chosen_lang' in locals() else 'auto')

            return JsonResponse({
                'ai_reply': fallback_response,
                'mood': 'Neutral',
                'stress_level': 3
            })

    return JsonResponse({'error': 'Invalid request method.'}, status=400)


@login_required
def chat_history(request, user_id=None):
    if not request.user.is_psychologist:
        messages.error(
            request, "Access denied. Only psychologists can view chat history.")
        return redirect('psychologistdashboard')

    # Get assigned users
    assigned_users = CustomUser.objects.filter(
        assignments__psychologist=request.user
    ).order_by('username')

    if user_id:
        try:
            selected_user = CustomUser.objects.get(id=user_id)

            # Get chat messages from Message model
            messages = Message.objects.filter(
                user=selected_user).order_by('created_at')

            # Prepare messages for display
            chat_messages = []
            for message in messages:
                chat_messages.append({
                    'sender': 'User' if message.sender == 'user' else 'Bot',
                    'content': message.text,
                    'timestamp': message.created_at.strftime('%b %d, %Y %H:%M')
                })

            # Get current mood
            current_mood = MoodInsight.objects.filter(
                user=selected_user).order_by('-created_at').first()

            context = {
                'selected_user': selected_user,
                'chat_messages': chat_messages,
                'assigned_users': assigned_users,
                'current_mood': current_mood
            }
            return render(request, 'chat_history.html', context)

        except CustomUser.DoesNotExist:
            messages.error(request, "User not found.")
            return redirect('chat_history')
    else:
        context = {
            'assigned_users': assigned_users
        }
        return render(request, 'chat_history.html', context)


@login_required
def mood_insights(request, user_id=None):
    if not request.user.is_psychologist:
        messages.error(
            request, "Access denied. Only psychologists can view mood insights.")
        return redirect('psychologistdashboard')

    # Get assigned users
    assigned_users = CustomUser.objects.filter(
        assignments__psychologist=request.user
    ).order_by('username')

    if user_id:
        try:
            selected_user = CustomUser.objects.get(id=user_id)

            # Get mood insights and user moods
            mood_insights = MoodInsight.objects.filter(
                user=selected_user).order_by('-created_at')
            user_moods = UserMood.objects.filter(
                user=selected_user).order_by('-created_at')

            # Calculate average confidence
            avg_confidence = mood_insights.aggregate(
                avg=models.Avg('confidence_score'))['avg'] or 0
            # Convert to percentage
            avg_confidence = round(avg_confidence * 100, 1)

            # Prepare data for charts
            moods = ['Happy', 'Calm', 'Neutral', 'Sad', 'Anxious']
            mood_counts = []
            for mood in moods:
                count = mood_insights.filter(mood=mood).count()
                mood_counts.append(count)

            # Get dates and mood values for trend chart (last 30 days)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)

            # Group insights by date
            mood_data = {}
            for insight in mood_insights:
                date_str = insight.created_at.strftime('%Y-%m-%d')
                if date_str not in mood_data:
                    mood_data[date_str] = {
                        'Happy': 0, 'Calm': 0, 'Neutral': 0, 'Sad': 0, 'Anxious': 0}
                mood_data[date_str][insight.mood] += 1

            # Prepare data for chart
            dates = []
            happy_values = []
            calm_values = []
            neutral_values = []
            sad_values = []
            anxious_values = []

            # Fill in data for each day in the last 30 days
            current_date = start_date
            while current_date <= end_date:
                date_str = current_date.strftime('%Y-%m-%d')
                dates.append(current_date.strftime('%b %d'))

                # Get mood counts for this date or use 0 if no data
                day_data = mood_data.get(date_str, {
                    'Happy': 0, 'Calm': 0, 'Neutral': 0, 'Sad': 0, 'Anxious': 0
                })

                happy_values.append(day_data['Happy'])
                calm_values.append(day_data['Calm'])
                neutral_values.append(day_data['Neutral'])
                sad_values.append(day_data['Sad'])
                anxious_values.append(day_data['Anxious'])

                current_date += timedelta(days=1)

            # Calculate total moods for percentage calculation
            total_moods = sum(mood_counts)
            if total_moods == 0:
                mood_percentages = [0] * len(moods)
            else:
                mood_percentages = [(count / total_moods)
                                    * 100 for count in mood_counts]

            context = {
                'selected_user': selected_user,
                'mood_insights': mood_insights,
                'user_moods': user_moods,
                'mood_labels': json.dumps(moods),
                'mood_counts': json.dumps(mood_counts),
                'mood_percentages': json.dumps(mood_percentages),
                'dates_labels': json.dumps(dates),
                'happy_values': json.dumps(happy_values),
                'calm_values': json.dumps(calm_values),
                'neutral_values': json.dumps(neutral_values),
                'sad_values': json.dumps(sad_values),
                'anxious_values': json.dumps(anxious_values),
                'assigned_users': assigned_users,
                'avg_confidence': avg_confidence
            }
            return render(request, 'mood_insights.html', context)

        except CustomUser.DoesNotExist:
            messages.error(request, "User not found.")
            return redirect('mood_insights')
    else:
        # Populate latest mood for each user
        for user in assigned_users:
            latest_mood = UserMood.objects.filter(
                user=user).order_by('-created_at').first()
            user.latest_mood = latest_mood.mood if latest_mood else 'Not available'

        context = {
            'assigned_users': assigned_users
        }
        return render(request, 'mood_insights.html', context)


@login_required
def psychologist_dashboard(request):
    if not request.user.is_psychologist:
        return redirect('userdashboard')

    # Get assigned users
    assigned_users = CustomUser.objects.filter(
        assignments__psychologist=request.user
    ).order_by('username')

    for user in assigned_users:
        latest_mood = UserMood.objects.filter(
            user=user).order_by('-created_at').first()
        user.latest_mood = latest_mood.mood if latest_mood else 'Not available'
        user.latest_stress_level = latest_mood.stress_level if latest_mood else 'N/A'

        latest_insight = MoodInsight.objects.filter(
            user=user).order_by('-created_at').first()
        user.latest_mood_confidence = latest_insight.confidence_score if latest_insight else None

    # Get recent reports
    reports = Report.objects.filter(
        user__assignments__psychologist=request.user
    ).order_by('-created_at')[:10]

    # Get counts for dashboard
    assigned_user_count = assigned_users.count()
    survey_count = MentalHealthSurvey.objects.filter(
        user__assignments__psychologist=request.user).count()
    chat_count = Message.objects.filter(
        user__assignments__psychologist=request.user).count()
    report_count = Report.objects.filter(
        user__assignments__psychologist=request.user).count()

    context = {
        'assigned_users': assigned_users,
        'reports': reports,
        'assigned_user_count': assigned_user_count,
        'survey_count': survey_count,
        'chat_count': chat_count,
        'report_count': report_count
    }
    return render(request, 'psychologistdashboard.html', context)


@login_required
def psychologist_profile(request):
    try:
        user_profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        # If profile does not exist, you can redirect or show error
        return redirect('register')  # or you can create a new profile

    context = {
        'user_profile': user_profile,
    }
    return render(request, 'psychologist_profile.html', context)


@login_required
def psychologist_edit_profile(request):
    try:
        user_profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        return redirect('register')

    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        profile_picture = request.FILES.get('profile_picture')

        user_profile.full_name = full_name
        user_profile.email = email
        user_profile.phone_number = phone_number
        if profile_picture:
            user_profile.profile_picture = profile_picture
        user_profile.save()

        messages.success(request, "Profile updated successfully!")
        return redirect('psychologist_profile')

    context = {
        'user_profile': user_profile,
    }
    return render(request, 'psychologist_edit_profile.html', context)


# views.py


@login_required
def user_report_view(request):
    user = request.user
    user_report = Report.objects.filter(
        user=user).order_by('-created_at').first()
    return render(request, 'user_report.html', {'report': user_report})

# members/views.py


def feedback_success(request):
    return render(request, 'feedback_success.html')


def contact_view(request):
    # You can replace 'contact.html' with the actual template for the contact page
    return render(request, 'contact.html')


def assign_psychologist_dynamic(user, message_text, mood, stress_level):
    """Automatically assign psychologist based on chat interaction."""
    # Only assign if not already assigned
    if Assignment.objects.filter(user=user).exists():
        return

    try:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        prompt = (
            f"Analyze the following user's message and emotional state:\n\n"
            f"Message: {message_text}\n"
            f"Detected Mood: {mood}\n"
            f"Stress Level: {stress_level}\n\n"
            f"Based on this, suggest a specialization: \n"
            f"- Trauma Specialist, Relationship Counselor, Anxiety Therapist, Sleep Therapist, General Psychologist.\n"
            f"Just respond with one specialization."
        )
        
        try:
            model = genai.GenerativeModel("gemini-2.0-flash")
            response = model.generate_content(prompt)
            specialization = response.text.strip().lower()
        except Exception:
            specialization = "general"
        
        # RESTRICTED ASSIGNMENT: Only these 4 psychologists (using core names to match DB)
        psychologist_map = {
            "trauma": "Amanda",
            "relationship": "James",
            "counsel": "James",
            "anxiety": "Emily",
            "stress": "Emily",
            "sleep": "Sarah",
            "child": "Sarah",
            "adhd": "Sarah"
        }

        # Default to James if no match
        psychologist_name = "James"
        
        for key, name in psychologist_map.items():
            if key in specialization:
                psychologist_name = name
                break
             
        try:
            # Try to get the specific psychologist
            psychologist = CustomUser.objects.filter(fullname__icontains=psychologist_name, role='psychologist').first()
            
            # If specific one not found, fallback to ANY of the allowed names
            if not psychologist:
                allowed_names = ["Emily", "Sarah", "James", "Amanda"]
                psychologist = CustomUser.objects.filter(fullname__in=allowed_names, role='psychologist').first()

        except Exception as e:
            print(f"Error finding psychologist: {e}")
            psychologist = None

        if psychologist:
            Assignment.objects.create(user=user, psychologist=psychologist)
            print(f"Automatically assigned {psychologist.fullname} to {user.username}")
        else:
            print("No suitable psychologist found from the allowed list.")
            
    except Exception as e:
        print(f"Error in automatic assignment: {e}")



def assign_psychologist_based_on_survey(survey_instance):
    """Use Gemini/GPT to recommend psychologist based on survey answers."""
    genai.configure(api_key=settings.GEMINI_API_KEY)
    
    prompt = (
        f"Analyze the following user's mental health survey:\\n\\n"
        f"Anxiety Level: {survey_instance.anxiety_level}\\n"
        f"Trauma Experience: {survey_instance.trauma_experience}\\n"
        f"Relationship Issues: {survey_instance.relationship_issues}\\n"
        f"Sleep Quality: {survey_instance.sleep_quality}\\n"
        f"Appetite Change: {survey_instance.appetite_change}\\n"
        f"Energy Level: {survey_instance.energy_level}\\n"
        f"Emotional Control: {survey_instance.emotional_control}\\n"
        f"Social Interaction: {survey_instance.social_interaction}\\n"
        f"Past Mental Health: {survey_instance.past_mental_health}\\n"
        f"Specific Concern: {survey_instance.specific_concern}\\n\\n"
        f"Based on the symptoms, suggest a specialization: \\n"
        f"- Trauma Specialist, Relationship Counselor, Anxiety Therapist, Sleep Therapist, General Psychologist etc.\\n"
        f"Just respond with one specialization."
    )
    model = genai.GenerativeModel("models/gemini-1.5-flash")
    response = model.generate_content(prompt)
    specialization = response.text.strip().lower()  # Basic mapping for demo
    if "trauma" in specialization:
        return "Dr. Amanda Blake"
    elif "relationship" in specialization:
        return "Dr. James Anderson"
    elif "anxiety" in specialization:
        return "Dr. Emily Carter"
    elif "sleep" in specialization:
        return "Dr. Sarah Mitchell"
    else:
        return "Dr. James Anderson"  # General fallback


@csrf_exempt
def submit_survey(request):
    if request.method == "POST":
        form = MentalHealthSurveyForm(request.POST)
        if form.is_valid():
            # Get or create the survey
            survey, created = MentalHealthSurvey.objects.get_or_create(
                user=request.user,
                defaults=form.cleaned_data
            )
            if not created:
                # Update existing survey
                for field, value in form.cleaned_data.items():
                    setattr(survey, field, value)
                survey.save()

            # Assign psychologist based on survey
            psychologist_name = assign_psychologist_based_on_survey(survey)

            # Fetch actual psychologist user
            try:
                psychologist = CustomUser.objects.get(fullname__icontains=psychologist_name, role='psychologist')
            except CustomUser.DoesNotExist:
                psychologist = CustomUser.objects.filter(role='psychologist').order_by('?').first()  # fallback

            if psychologist:
                Assignment.objects.filter(user=request.user).delete()
                Assignment.objects.create(
                    user=request.user,
                    psychologist=psychologist
                )
                psychologist_name = psychologist.fullname
            else:
                psychologist_name = "a mental health professional"

            return render(request, "thank_you.html", {"psychologist_name": psychologist_name})

        # Return form with errors if invalid, or handle error page
        messages.error(request, "Please check the form details.")
        return render(request, "survey_form.html", {'form': form})
    
    return render(request, "survey_form.html")  # GET request returns the form

@login_required
def book_appointment(request):
    if request.user.role != 'user':
        return redirect('home')

    # Get the assigned psychologist (safely grabbing the latest if any edge cases occur)
    assignment = Assignment.objects.filter(user=request.user).order_by('-assigned_at').first()
    if not assignment:
        messages.warning(request, "Please submit the mental health survey first, so we can assign you a psychologist before booking an appointment.")
        return redirect('survey_form')

    if request.method == 'POST':
        date_str = request.POST.get('date')
        time_str = request.POST.get('time')

        if not date_str or not time_str:
            messages.error(request, "Please provide both date and time.")
            return render(request, 'book_appointment.html', {'psychologist': assignment.psychologist})

        try:
            # Generate a unique Jitsi Meet link
            room_id = str(uuid.uuid4())
            meet_link = f"https://meet.jit.si/MindEase-Session-{room_id}"

            Appointment.objects.create(
                user=request.user,
                psychologist=assignment.psychologist,
                date=date_str,
                time=time_str,
                meet_link=meet_link,
                status='Scheduled'
            )

            # Send real-time notification to the psychologist
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'psychologist_{assignment.psychologist.id}',
                {
                    'type': 'send_notification',
                    'message': f'New appointment scheduled by {request.user.fullname} on {date_str} at {time_str}'
                }
            )

            messages.success(request, f"Appointment successfully scheduled with {assignment.psychologist.fullname}.")
            return redirect('userdashboard')
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")

    # Get upcoming appointments
    upcoming_appointments = Appointment.objects.filter(
        user=request.user,
        status='Scheduled'
    ).order_by('date', 'time')

    return render(request, 'book_appointment.html', {
        'psychologist': assignment.psychologist,
        'upcoming_appointments': upcoming_appointments
    })

@login_required
def psychologist_appointments(request):
    if request.user.role != 'psychologist':
        return redirect('home')

    appointments = Appointment.objects.filter(psychologist=request.user).order_by('date', 'time')
    return render(request, 'psychologist_appointments.html', {'appointments': appointments})

@login_required
def video_call(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)

    # Allow access only to the user or the psychologist associated with the appointment
    if request.user != appointment.user and request.user != appointment.psychologist:
        return redirect('no_access')

    # Ensure the appointment is scheduled
    if appointment.status != 'Scheduled':
        messages.warning(request, "This appointment is no longer active.")
        if request.user.role == 'psychologist':
            return redirect('psychologist_appointments')
        return redirect('userdashboard')

    return render(request, 'video_call.html', {'appointment': appointment})


