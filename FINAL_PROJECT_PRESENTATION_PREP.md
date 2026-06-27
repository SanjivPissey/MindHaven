# Final Project Presentation Preparation Guide

## 1. Project Overview
**Title:** MindHaven (Mental Health Support System)
**Goal:** To provide accessible, immediate, and intelligent mental health support using AI and professional psychologist monitoring.
**Core Tech Stack:**
-   **Backend:** Django (Python)
-   **Frontend:** HTML5, CSS3, JavaScript (Chart.js for visualizations)
-   **AI Engine:** Google Gemini API (Models: `gemini-flash-latest` / `gemini-pro-latest`)
-   **Database:** SQLite (Dev) / PostgreSQL (Prod ready)

---

## 2. Key Topics to Cover

### A. The Problem Statement
-   Mental health resources are often expensive or inaccessible.
-   Stigma prevents many from seeking initial help.
-   Need for 24/7 immediate support + professional oversight.

### B. Solution & Innovation
-   **Hybrid Approach:** AI provides immediate "First Aid" support, while human psychologists handle deeper therapy and monitoring.
-   **Real-time Analysis:** The system doesn't just chat; it analyzes *Mood* and *Stress Levels* from the text.
-   **Crisis Intevention:** Specialized prompts detect suicidal/self-harm keywords and shift the AI into a "Crisis Support" mode immediately.

### C. Core Modules
1.  **AI Chatbot:** Empathetic, context-aware conversations.
2.  **Psychologist Dashboard:** View assigned users, read chat history (for context), view mood graphs.
3.  **Mood Tracking:** Users can track their emotional state over time.
4.  **Resource Library:** Curated content for self-help (Yoga, Music, etc.).

---

## 3. Important Code Snippets (For Slides/Demo)

### Snippet 1: AI Crisis Detection & Response Logic
*Location: `members/views.py`*
**Why it's important:** Shows how the basic safety mechanism works. It detects dangerous keywords and prompts the AI to be extra careful and supportive.

```python
# Detect if this is a serious/crisis situation
user_message_lower = user_message.lower()
is_crisis = any(keyword in user_message_lower for keyword in [
    'die', 'dying', 'kill myself', 'suicide', 'end it all', 
    'self harm', 'hurt myself', 'abuse', 'trauma'
])

# Specialized Prompting for Crisis
if is_crisis:
    prompt = f"""You are a deeply compassionate mental health support chatbot...
    The user is experiencing a serious crisis...
    CRITICAL GUIDELINES:
    1. Start with IMMEDIATE CARE AND COMFORT...
    2. Acknowledge the FULL DEPTH of their pain...
    3. If appropriate, gently suggest professional support...
    """
```

### Snippet 2: Mood Analysis & Integration
*Location: `members/views.py`*
**Why it's important:** Demonstrates that the chatbot isn't just text-in-text-out; it captures structured data (mood/stress) from unstructured conversation.

```python
# In ai_chat_support function
try:
    # Save bot response
    Message.objects.create(user=request.user, sender='bot', text=ai_response)

    # Save mood insight automatically derived from chat
    MoodInsight.objects.create(
        user=request.user,
        mood=mood,              # value from detect_mood()
        confidence_score=0.8,
        stress_level=stress,    # value from detect_stress_level()
        created_at=timezone.now()
    )
    
    # Auto-assign psychologist if needed based on stress
    assign_psychologist_dynamic(request.user, user_message, mood, stress)

except Exception as save_error:
    print(f"Error saving chat data: {save_error}")
```

### Snippet 3: Psychologist Mood Dashboard Data
*Location: `members/views.py` (view: `mood_insights`)*
**Why it's important:** Shows how the backend prepares data for the frontend visualization (Charts), enabling professionals to make data-driven decisions.

```python
# Calculate mood trends for the last 30 days
end_date = datetime.now()
start_date = end_date - timedelta(days=30)

# Group insights by date for Chart.js
mood_data = {}
for insight in mood_insights:
    date_str = insight.created_at.strftime('%Y-%m-%d')
    if date_str not in mood_data:
        mood_data[date_str] = { 'Happy': 0, 'Calm': 0, 'Anxious': 0, ... }
    mood_data[date_str][insight.mood] += 1

# Data passed to template
context = {
    'mood_percentages': json.dumps(mood_percentages),
    'dates_labels': json.dumps(dates),
    'happy_values': json.dumps(happy_values),
    # ... other mood values
}
```

---

## 4. Possible QA Questions & Answers

**Q: How does the AI know what to say?**
**A:** We use the Google Gemini API. We feed it a "System Prompt" (like a set of instructions) that defines its persona as a compassionate therapist. We also provide the last 15 messages so it remembers the conversation context.

**Q: Is user data private?**
**A:** Yes. Users have their own accounts. However, mapped Psychologists *can* view chat history to provide better care. This is a design choice for a "Clinical Support" tool rather than a purely private diary.

**Q: How is the mood detected?**
**A:** Currently, we use a rule-based/keyword system (or a secondary light AI call) to classify the user's message into categories like 'Happy', 'Sad', 'Anxious', etc.

**Q: What happens if the internet goes down?**
**A:** The AI chat requires internet for the API. However, the Resource Library (Yoga/Music) and past Dashboard data are accessible if cached, though primarily it is an online web app.

---

## 5. Future Enhancements (To mention at the end)
1.  **Voice Interaction:** Adding Speech-to-Text for easier communication.
2.  **Mobile App:** Converting the web app to React Native/Flutter.
3.  **Emergency API:** Integration with local emergency services APIs for immediate dispatch during detected high-crisis events.
