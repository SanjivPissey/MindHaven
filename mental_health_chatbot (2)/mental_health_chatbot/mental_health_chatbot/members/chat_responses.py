"""
Hybrid chat response system - combines rule-based responses with API fallback.
Supports both Hindi and English.
"""
import re
import random

# --- Hindi Rule-Based Responses ---
HINDI_RULE_BASED_RESPONSES = {
    'greeting': [
        "नमस्ते! मैं यहाँ हूँ आपकी बात सुनने के लिए। आज आप कैसा महसूस कर रहे हैं?",
        "हेलो! मुझे खुशी है कि आपने संपर्क किया। बिना किसी निर्णय के मैं यहाँ आपकी बात सुनने के लिए तैयार हूँ।",
        "स्वागत है! मैं आपके लिए यहाँ हूँ। जो भी आप महसूस कर रहे हैं, मुझे बताइए।",
    ],
    'anxiety': [
        "मैं समझ सकता/सकती हूँ कि चिंता बहुत भारी लग सकती है। आप जो महसूस कर रहे हैं वो बिल्कुल सच है और आप अकेले नहीं हैं। एक गहरी साँस लीजिए — मैं यहाँ हूँ। क्या आप मुझे बता सकते हैं कि सबसे ज़्यादा किस चीज़ की चिंता है?",
        "घबराहट और चिंता बहुत कठिन होती है, और मैं देख सकता/सकती हूँ कि आप मुश्किल वक्त से गुज़र रहे हैं। आपकी भावनाएँ बिल्कुल सही हैं। आगे क्या हो रहा है, मुझे और बताइए?",
    ],
    'sad': [
        "मुझे बहुत दुख है कि आप इस वक्त उदास महसूस कर रहे हैं। आपकी भावनाएँ बिल्कुल सच हैं और मैं बिना किसी फैसले के यहाँ सुनने के लिए हूँ। क्या आप मुझे बता सकते हैं कि क्या हुआ?",
        "उदास महसूस करना बहुत भारी होता है, और मैं चाहता/चाहती हूँ कि आप जानें — ठीक न होना ठीक है। आप अकेले नहीं हैं। सबसे ज़्यादा क्या तकलीफ दे रहा है आपको?",
    ],
    'stress': [
        "लगता है आप बहुत दबाव में हैं, और यह महसूस करना बिल्कुल स्वाभाविक है। आप सही कर रहे हैं जो बात कर रहे हैं। अभी सबसे बड़ा तनाव किस वजह से है?",
        "तनाव मानसिक और शारीरिक दोनों तरह से थका देता है। आपकी भावनाएँ पूरी तरह से सही हैं। क्या मैं आपकी मदद कर सकता/सकती हूँ — बताइए क्या हो रहा है?",
    ],
    'lonely': [
        "अकेलापन बहुत कठिन होता है और मैं समझ सकता/सकती हूँ कि यह कितना दर्दनाक हो सकता है। आप अकेले नहीं हैं — मैं यहाँ हूँ। आप किस तरह का जुड़ाव ढूंढ रहे हैं?",
        "अकेलेपन की भावना बहुत असली होती है। इसे स्वीकार करने की हिम्मत दिखाई — यही बड़ी बात है। बताइए, क्या हो रहा है आपके जीवन में?",
    ],
    'tired': [
        "लगता है आप बहुत थके हुए हैं — शरीर से भी और मन से भी। यह बिल्कुल असली थकान है। क्या चीज़ आपको सबसे ज़्यादा थका रही है?",
        "थकान हर चीज़ को और भारी बना देती है। आपको इसे महसूस करने में कोई शर्म नहीं है। आराम की ज़रूरत है — कौन सी चीज़ आपकी ऊर्जा ले रही है?",
    ],
    'angry': [
        "गुस्सा एक बिल्कुल सही भावना है। लगता है किसी बात ने आपको सच में तकलीफ दी है। मैं यहाँ हूँ, बताइए — क्या हुआ?",
        "गुस्सा अक्सर दर्द या निराशा से आता है। आपकी भावनाएँ सच्ची हैं। क्या हुआ जिसने यह भावना जगाई?",
    ],
    'crisis': [
        "मुझे बहुत दुख है कि आप इस वक्त इतने दर्द में हैं। आप बहुत हिम्मती हैं कि बात कर रहे हैं। आप अकेले नहीं हैं — मैं यहाँ हूँ। क्या आप मुझे थोड़ा और बता सकते हैं कि क्या हो रहा है?",
        "आपका दर्द बिल्कुल असली है और आप मायने रखते हैं। यह वक्त बहुत मुश्किल है, लेकिन आप अकेले नहीं हैं। मुझे बताइए — क्या चल रहा है?",
    ],
    'default': [
        "मैं सुन रहा/रही हूँ और जो आप कह रहे हैं वो मेरे लिए मायने रखता है। क्या आप थोड़ा और बता सकते हैं कि आप कैसा महसूस कर रहे हैं?",
        "आपकी बात सुनकर अच्छा लगा। आपकी भावनाएँ पूरी तरह से सही हैं। मुझे और बताइए — मैं समझना चाहता/चाहती हूँ।",
    ],
}

# --- English Rule-Based Responses ---
ENGLISH_RULE_BASED_RESPONSES = {
    'greeting': [
        "Hello! I'm here to listen and support you with whatever you're going through. How are you feeling today, and what's been on your mind?",
        "Hi there! I'm really glad you reached out. I'm here to listen without judgment - what would you like to talk about?",
        "Welcome! I'm here for you. Take your time - I'm ready to hear about whatever you're experiencing or feeling.",
    ],
    'anxiety': [
        "I can understand that anxiety can feel completely overwhelming, and I want you to know that what you're experiencing is valid. You're not alone in this feeling - many people struggle with anxiety, and it takes real courage to reach out. Take a deep breath with me. What specific situation or thought is causing you the most anxiety right now?",
        "Anxiety can be incredibly tough to manage, and I can hear that you're going through something difficult. Your feelings matter, and it's okay to feel this way. Remember, these feelings won't last forever, even though they might feel overwhelming right now. Can you tell me more about what's making you feel anxious?",
    ],
    'sad': [
        "I'm so sorry you're feeling sad right now. Your feelings are completely valid and important, and you have every right to feel the way you do. I'm here to listen without judgment. Can you tell me more about what's making you feel this way? I want to understand what you're going through.",
        "Feeling sad can be really difficult, and I want you to know that it's okay to not be okay. Your emotions matter, and I'm here to support you through this. What's been weighing most heavily on your mind?",
    ],
    'stress': [
        "I can understand that stress can feel completely overwhelming, and it sounds like you're dealing with a lot right now. Your feelings are completely valid. Let's take this one step at a time. What's the main thing that's causing you the most stress right now?",
        "Stress can really take a toll on both your mental and physical well-being. You're doing the right thing by reaching out and acknowledging what you're feeling. What would help you feel less overwhelmed right now?",
    ],
    'lonely': [
        "Feeling lonely can be incredibly difficult and isolating, and I want you to know that your feelings are completely valid. I'm here with you right now, and I want you to know that you matter. What makes you feel most connected to others?",
        "Loneliness is one of the hardest emotions to experience, and I can hear that you're struggling with this. You're not weak for experiencing it. What kind of connection or support are you looking for?",
    ],
    'tired': [
        "It sounds like you're feeling completely exhausted, and I want you to know that I understand how draining that can be. What's been keeping you up or draining your energy? Is it more physical exhaustion, emotional exhaustion, or both?",
        "Exhaustion can make everything feel so much harder. Your body and mind need rest, and there's no shame in acknowledging when you're drained. What might be causing this?",
    ],
    'angry': [
        "Anger is a completely valid emotion, and it sounds like something has really triggered these feelings for you. What's making you feel this way? I'm here to listen and understand.",
        "I can understand that you're feeling angry right now, and I want you to know that your feelings are valid. Anger often comes from a place of hurt or frustration. What triggered your anger?",
    ],
    'crisis': [
        "I'm so sorry you're going through this right now. Your pain is real and valid, and I want you to know that I'm here with you in this moment. You don't have to face this alone - there are people who care about you. Would you like to tell me more about what's happening?",
        "I hear the deep pain in your words, and I want you to know that you matter - truly, you do. You're not alone in this - I'm here. Can you tell me a bit more about what's going on?",
    ],
    'default': [
        "I hear you, and I want you to know that what you're sharing matters to me. Your feelings are completely valid, and I'm here to listen and understand. Can you tell me more about what you're experiencing?",
        "Thank you for sharing that with me. Your emotions are important, and you're not alone in this. Can you help me understand a bit more about what's going on?",
    ],
}

# --- Hindi keyword sets ---
HINDI_KEYWORDS = {
    'crisis': [
        'मरना', 'मर जाना', 'खुदकुशी', 'suicide', 'जीना नहीं', 'जिंदगी खत्म',
        'खुद को नुकसान', 'दर्द', 'मदद', 'बचाओ',
    ],
    'greeting': [
        'नमस्ते', 'हेलो', 'हाय', 'हेय', 'सुप्रभात', 'शुभ संध्या',
    ],
    'anxiety': [
        'घबराहट', 'चिंता', 'डर', 'परेशान', 'बेचैन', 'नर्वस', 'anxiety',
    ],
    'sad': [
        'उदास', 'दुखी', 'रोना', 'रो', 'तकलीफ', 'दर्द', 'दुख', 'बुरा',
    ],
    'stress': [
        'तनाव', 'stress', 'दबाव', 'थकान', 'बहुत ज़्यादा',
    ],
    'lonely': [
        'अकेला', 'अकेलापन', 'एकांत', 'कोई नहीं', 'कोई साथ नहीं',
    ],
    'tired': [
        'थका', 'थकान', 'नींद', 'सोना', 'आराम',
    ],
    'angry': [
        'गुस्सा', 'क्रोध', 'चिढ़', 'नाराज़', 'नाराज',
    ],
}


def _contains_hindi(text):
    """Returns True if text contains Devanagari script or common Hindi/Hinglish words."""
    # Devanagari unicode range: \u0900-\u097F
    if re.search(r'[\u0900-\u097F]', text):
        return True
    # Common Hinglish words that are clearly Hindi
    hinglish_words = [
        'mujhe', 'mera', 'meri', 'main', 'hoon', 'hai', 'ho', 'tha', 'thi',
        'bahut', 'acha', 'accha', 'theek', 'thoda', 'kya', 'kaise', 'kyun',
        'nahi', 'nahin', 'haan', 'abhi', 'kal', 'aaj', 'yaar', 'bhai',
        'behen', 'dost', 'pyaar', 'zindagi', 'pareshan', 'dukhi', 'udaas',
        'khush', 'takleef', 'rone', 'dard', 'akela', 'akele', 'gussa',
        'chinta', 'ghabrana', 'tanaav', 'thaka', 'neend', 'pagal',
    ]
    text_lower = text.lower()
    return any(word in text_lower for word in hinglish_words)


def detect_keywords(message):
    """Detect keywords in user message to match with rule-based responses. Returns (category, is_hindi)."""
    message_lower = message.lower()
    is_hindi = _contains_hindi(message)

    # Choose the right keyword set
    if is_hindi:
        # Check Hindi-specific keywords
        for category, keywords in HINDI_KEYWORDS.items():
            if any(kw in message_lower or kw in message for kw in keywords):
                return category, True

    # English keywords (also used as fallback for Hinglish)
    crisis_keywords = [
        'die', 'dying', 'kill myself', 'suicide', 'end it all', 'not worth living',
        'want to die', 'better off dead', 'give up', 'hopeless', 'no point',
        'self harm', 'hurt myself', 'abuse', 'trauma', 'hit me', 'beat me', 'attacked'
    ]
    if any(keyword in message_lower for keyword in crisis_keywords):
        return 'crisis', is_hindi

    if any(word in message_lower for word in ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']):
        return 'greeting', is_hindi

    if any(word in message_lower for word in ['anxious', 'anxiety', 'worried', 'worries', 'panic', 'nervous', 'overwhelmed']):
        return 'anxiety', is_hindi

    if any(word in message_lower for word in ['sad', 'depressed', 'down', 'unhappy', 'miserable', 'hopeless', 'empty']):
        return 'sad', is_hindi

    if any(word in message_lower for word in ['stressed', 'stress', 'pressure', 'overwhelmed', 'burnt out', 'burnout']):
        return 'stress', is_hindi

    if any(word in message_lower for word in ['lonely', 'alone', 'isolated', 'disconnected', 'no one', 'nobody']):
        return 'lonely', is_hindi

    if any(word in message_lower for word in ['tired', 'exhausted', 'drained', 'fatigued', 'worn out', 'sleepy']):
        return 'tired', is_hindi

    if any(word in message_lower for word in ['angry', 'mad', 'furious', 'irritated', 'frustrated', 'annoyed']):
        return 'angry', is_hindi

    return 'default', is_hindi


def get_rule_based_response(user_message, forced_lang=None):
    """Get a rule-based response based on keywords, respecting the forced language if set."""
    category, is_hindi = detect_keywords(user_message)

    # If the user explicitly chose a language, honour it
    if forced_lang == 'hi':
        use_hindi = True
    elif forced_lang == 'en':
        use_hindi = False
    else:
        use_hindi = is_hindi  # auto-detect

    if use_hindi:
        responses = HINDI_RULE_BASED_RESPONSES.get(category, HINDI_RULE_BASED_RESPONSES['default'])
    else:
        responses = ENGLISH_RULE_BASED_RESPONSES.get(category, ENGLISH_RULE_BASED_RESPONSES['default'])
    return random.choice(responses)


def should_use_api(message, has_conversation_history=False):
    """Determine if we should use API for empathetic, context-aware responses."""
    message_lower = message.lower()

    # ALWAYS use API if we have conversation history
    if has_conversation_history:
        return True

    # Use API for messages with substantial content (more than a few words)
    if len(message.split()) > 5:
        return True

    # Use API for any Hindi content
    if _contains_hindi(message):
        return True

    # CRITICAL: Use API for serious mental health concerns
    serious_concerns = [
        'die', 'dying', 'kill myself', 'suicide', 'end it all', 'not worth living',
        'want to die', 'better off dead', 'give up', 'hopeless', 'no point',
        'self harm', 'hurt myself', 'cut myself', 'abuse', 'trauma', 'assault',
        'hit me', 'beat me', 'attacked', 'violent', 'scared for my life'
    ]
    if any(concern in message_lower for concern in serious_concerns):
        return True

    # Use API for any emotional language
    emotional_patterns = [
        r'\b(feel|feeling|feelings|emotion|emotional|hurt|pain|sad|happy|angry|anxious|worried|scared|afraid|frustrated|overwhelmed|stressed|lonely|tired|exhausted)\b',
        r'\b(relationship|trauma|abuse|suicide|self-harm|therapy|counseling|medication|help|support|struggling|difficult|hard|tough|problem|issue|concern)\b',
        r'\b(why|how|what should|advice|help me understand|going through|experiencing|dealing with)\b',
    ]
    for pattern in emotional_patterns:
        if re.search(pattern, message, re.IGNORECASE):
            return True

    # Use API for any message that's not just a simple greeting
    simple_greetings = ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening']
    if not any(greeting in message_lower for greeting in simple_greetings):
        return True

    return False
