import json
import re
import requests
from django.conf import settings

from backend.helpers import refine_sentiment


def send_whats_app_message(instance, token, number, message):
    """
    Send a WhatsApp message using the WAAPI API
    Args:
        instance: WhatsApp instance ID
        token: WAAPI API token
        number: Recipient's phone number
        message: Message to send
    Returns:
        Response from the WAAPI API
    """

    url = f"https://waapi.app/api/v1/instances/{instance}/client/action/send-message"

    payload = {"chatId": f"{number}@c.us", "message": message, "previewLink": True}
    headers = {
        "authorization": f"Bearer {token}",
        "accept": "application/json",
        "content-type": "application/json",
    }
    response = requests.post(url, json=payload, headers=headers)
    print("Status code", response.status_code)
    return response.json()


def transcribe_audio_file(file_path, language="english"):
    """
    Transcribe an audio file using the LemonFox AI API

    Args:
        file_path: Path to the audio file
        api_key: LemonFox API key
        language: Language of the audio (default: english)

    Returns:
        The transcribed text or None if there was an error
    """

    api_key = settings.LEMON_FOX_API_KEY
    url = "https://api.lemonfox.ai/v1/audio/transcriptions"

    headers = {"Authorization": f"Bearer {api_key}"}

    data = {"language": language, "response_format": "json"}

    files = {"file": open(file_path, "rb")}

    try:
        response = requests.post(url, headers=headers, files=files, data=data)
        response.raise_for_status()
        result = response.json()

        # Extract the transcribed text from the result
        if "text" in result:
            return result["text"]
        else:
            print(f"No text found in transcription result: {result}")
            return None

    except Exception as e:
        print(f"Error transcribing audio: {e}")
        return None
    finally:
        files["file"].close()


def analyze_review_with_groq(conversation):
    """
    Use Groq API to analyze a review and extract sentiment, product name, emotions, and key feedback
    """

    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    prompt = f"""
        Analyze the following multi-turn customer service conversation related to food:

        \"\"\"\n{conversation}\n\"\"\"

        Return a valid JSON with this structure:
        {{
            "sentiment": "[positive/negative/neutral]",
            "product_name": ["product1", "product2"],
            "emotions": ["emotion1", "emotion2"],
            "keywords": ["keyword1", "keyword2"]
        }}

        Do not add any explanations or formatting outside the JSON.
    """

    payload = {
        "model": "llama3-8b-8192",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
    }

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        result = response.json()

        response_text = result["choices"][0]["message"]["content"]
        match = re.search(r"\{[\s\S]*\}", response_text)

        if not match:
            return {"error": "No JSON in response", "raw": response_text}

        parsed = json.loads(match.group())
        parsed["sentiment"] = refine_sentiment(
            parsed.get("sentiment", ""), parsed.get("emotions", [])
        )

        return parsed

    except Exception as e:
        error_msg = f"API request failed: {str(e)}"

        if hasattr(e, "response") and e.response is not None:
            try:
                error_details = e.response.json()
                error_msg += f" - Details: {json.dumps(error_details)}"
            except:
                error_msg += f" - Response: {e.response.text}"

        return {"error": error_msg}


def create_next_question_for_order(template_questions):
    template_questions = template_questions.order_by("priority")
    turn = template_questions.count()

    conversation_history = ""
    for i in range(turn):
        if template_questions[i].is_question_answered:
            assistant_questions = f"Assistant: {template_questions[i].question}"
            user_answers = f"User: {template_questions[i].answer}"
            conversation_history += f"{assistant_questions}\n{user_answers}\n"

    prompt = f"""
        You're a polite assistant collecting customer feedback at a restaurant.

        Rules:
        - Keep it short, warm, natural (no robotic tone).
        - In the 1st and 2nd turns: acknowledge the feedback + ask ONE polite, helpful follow-up question.
        - In the 3rd turn: wrap up based on overall tone of the conversation.

        Wrap-up logic:
        - If the customer feedback has been mostly negative or mixed: say something like "We'll work on this, hope next visit is better, and offer 15% off."
        - If the feedback has been mostly positive: say something like "Thanks! We'd love if you could leave us a 5-star Google review."

        Avoid:
        - Repeating phrases like "didn't meet expectations" or "sorry to hear" every time.
        - Asking more questions on the 3rd turn.

        Example (tone):
        User: The fries were cold.
        Assistant: Thanks for letting us know! Was it just the fries, or was the rest of your meal okay?

        Conversation so far:
        {conversation_history}
        (Turn {turn}/3)

        Your reply:
    """

    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "llama3-8b-8192",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
    }

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload
    )
    question = response.json()["choices"][0]["message"]["content"].strip()

    return question
