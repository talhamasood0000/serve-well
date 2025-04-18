import json
import requests
from django.conf import settings


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


def analyze_review_with_groq(review_text):
    """
    Use Groq API to analyze a review and extract sentiment, product name, emotions, and key feedback
    """

    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    prompt = f"""
        Analyze this product review: \"{review_text}\"
        You must respond in valid JSON format with exactly this structure:
        {{
            \"sentiment\": \"[positive/negative/neutral]\",
            \"product_name\": \"[product name]\",
            \"emotions\": [\"emotion1\", \"emotion2\"],
            \"key_feedback\": [\"point 1\", \"point 2\"]
        }}
        Do not include any explanations, markdown formatting, or text outside the JSON structure.
        For emotions, identify the primary emotions expressed (e.g., satisfaction, frustration, disappointment, joy, anger, surprise, etc.).
        Guidelines for product name:
        - Only include actual product names mentioned in the review (e.g., "Big Mac", "Oreo McFlurry", "fries").
        - If multiple products are mentioned, include them all in the list.
        - If no specific product is mentioned, use ["Unknown"].
        - Keep the JSON clean — no markdown, explanations, or extra text.
    """
    
    payload = {
        "model": "llama3-8b-8192",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1
    }
    
    try:
        response = requests.post("https://api.groq.com/openai/v1/chat/completions",
                                headers=headers,
                                json=payload)
        response.raise_for_status()
        result = response.json()

        analysis_text = result["choices"][0]["message"]["content"]
        
        try:
            analysis_json = json.loads(analysis_text)
            return analysis_json
        except json.JSONDecodeError as e:
            return {"error": f"Failed to parse Groq response as JSON: {str(e)}", "raw_response": analysis_text}

    except requests.exceptions.RequestException as e:
        error_msg = f"API request failed: {str(e)}"

        if hasattr(e, 'response') and e.response is not None:
            try:
                error_details = e.response.json()
                error_msg += f" - Details: {json.dumps(error_details)}"
            except:
                error_msg += f" - Response: {e.response.text}"
                
        return {"error": error_msg}
