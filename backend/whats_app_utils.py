import requests


def send_whats_app_message(instance, token, number, message):
    url = f"https://waapi.app/api/v1/instances/{instance}/client/action/send-message"

    payload = {
        "chatId": f"{number}@c.us",
        "message": message,
        "previewLink": True
    }
    headers = {
        "authorization": f"Bearer {token}",
        "accept": "application/json",
        "content-type": "application/json"
    }
    response = requests.post(url, json=payload, headers=headers)
    print("Status code", response.status_code)
    return response.json()
