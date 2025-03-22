import requests


def send_whats_app_message(instance, number, message):

    url = f"https://waapi.app/api/v1/instances/{instance}/client/action/send-message"

    payload = {
        "chatId": number,
        "message": message
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json"
    }
    response = requests.post(url, json=payload, headers=headers)

    print(response.text)

    return response.json()