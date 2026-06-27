import google.generativeai as genai
from django.conf import settings
import re

# Central generation client config
genai.configure(api_key=settings.GEMINI_API_KEY)

def get_gemini_model():
    """Helper to try flash then fallback to pro."""
    try:
        return genai.GenerativeModel('gemini-2.0-flash')
    except Exception:
        return genai.GenerativeModel('gemini-1.5-flash')

def detect_mood(message):
    # 1. Try AI-based detection first
    try:
        model = get_gemini_model()
        prompt = f"""
        Analyze the following message and determine the primary emotion.
        Return only the emotion word (Happy, Calm, Neutral, Sad, Anxious).
        
        Message: {message}
        Emotion:"""

        response = model.generate_content(prompt)
        emotion = response.text.strip() if response and response.text else "Neutral"

        # Extract only valid emotion word using regex
        match = re.search(
            r'\b(Happy|Calm|Neutral|Sad|Anxious)\b', emotion, re.IGNORECASE)
        if match:
            return match.group(1).capitalize()  # Capitalize for consistency
    except Exception as e:
        print(f"AI Mood Detection Error (falling back to keywords): {e}")

    # 2. Keyword-based fallback (English + Hindi/Hinglish)
    message = message.lower()
    if any(word in message for word in [
        'anxious', 'worried', 'panic', 'stress', 'fear', 'scared',
        'घबराहट', 'चिंता', 'डर', 'परेशान', 'बेचैन', 'ghabrana', 'chinta', 'dar',
    ]):
        return "Anxious"
    elif any(word in message for word in [
        'sad', 'depressed', 'low', 'cry', 'lonely', 'unhappy',
        'उदास', 'दुखी', 'रोना', 'अकेला', 'तकलीफ', 'udaas', 'dukhi', 'rone', 'akela',
    ]):
        return "Sad"
    elif any(word in message for word in [
        'happy', 'excited', 'great', 'joy', 'good', 'wonderful',
        'खुश', 'खुशी', 'अच्छा', 'बढ़िया', 'khush', 'khushi', 'accha',
    ]):
        return "Happy"
    elif any(word in message for word in [
        'relaxed', 'calm', 'peaceful', 'zen', 'chill',
        'शांत', 'शांति', 'ठीक', 'shant', 'theek',
    ]):
        return "Calm"

    return "Neutral"

def detect_stress_level(message):
    # 1. Try AI-based detection first
    try:
        model = get_gemini_model()
        prompt = f"""
        Analyze the following message and determine the stress level on a scale of 1–5.
        1 = Very low stress
        5 = Very high stress
        Return only the number.
        
        Message: {message}
        Stress Level:"""

        response = model.generate_content(prompt)
        text = response.text.strip() if response and response.text else "3"

        # Extract just the first number from the response
        match = re.search(r'\b([1-5])\b', text)
        if match:
            return int(match.group(1))
    except Exception as e:
        print(f"AI Stress Detection Error (falling back to keywords): {e}")

    # 2. Keyword-based fallback (English + Hindi/Hinglish)
    message = message.lower()
    if any(word in message for word in [
        'panic', 'crisis', 'emergency', 'help', 'suicide',
        'मरना', 'खुदकुशी', 'बचाओ', 'bachao',
    ]):
        return 5
    elif any(word in message for word in [
        'stressed', 'anxious', 'pressure', 'overwhelmed',
        'तनाव', 'घबराहट', 'परेशान', 'tanaav', 'ghabrana', 'pareshan',
    ]):
        return 4
    elif any(word in message for word in [
        'fine', 'meh', 'neutral', 'okay',
        'ठीक', 'सामान्य', 'theek', 'samanya',
    ]):
        return 3
    elif any(word in message for word in [
        'calm', 'relaxed', 'better',
        'शांत', 'बेहतर', 'shant', 'behtar',
    ]):
        return 2
    elif any(word in message for word in [
        'peaceful', 'chill', 'happy', 'great',
        'खुश', 'अच्छा', 'बढ़िया', 'khush', 'accha',
    ]):
        return 1

    return 3

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
