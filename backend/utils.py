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
