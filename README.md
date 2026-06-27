# MindHaven (Mental Health Support System)

**MindHaven** is a mental health support system built primarily with Python (Django) and integrated with the Google Gemini AI. 

## Goal
To provide accessible, immediate, and intelligent mental health support using a hybrid approach of AI "first aid" and professional human oversight.

## Core Features
1. **AI Chatbot**: Provides context-aware, empathetic conversations using the Gemini API. It analyzes the user's messages to track mood and stress levels, and features a **Crisis Detection** mechanism that shifts the AI into a specialized support mode if it detects keywords related to self-harm or severe distress.
2. **Psychologist Dashboard**: Allows human professionals to monitor assigned users, read their chat histories for context, and view visual graphs of the user's tracked mood trends over time.
3. **Mood Tracking & Analytics**: Automatically infers the user's emotional state from their conversations to track their mood and stress levels over a 30-day period.
4. **Resource Library**: Offers curated self-help content, like yoga or music, to supplement the chat.

## Tech Stack
- **Backend**: Django (Python)
- **Frontend**: HTML5, CSS3, JavaScript (with Chart.js for visualization)
- **AI Engine**: Google Gemini API (Models: `gemini-flash-latest` / `gemini-pro-latest`)
- **Database**: SQLite / PostgreSQL
