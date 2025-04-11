import base64
import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import datetime

from backend.models import Company
from backend.tasks import process_next_step_for_order


@csrf_exempt
def whatsapp_webhook(request, security_token):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)
    
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    instance_id = body.get('instanceId')
    event_name = body.get('event')
    event_data = body.get('data')

    if not all([security_token, instance_id, event_name, event_data]):
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    company = Company.objects.filter(instance_id=instance_id).first()
    if not company:
        return JsonResponse({'error': 'Invalid instance ID'}, status=400)

    if company.webhook_token != security_token:
        return JsonResponse({'error': 'Authentication failed'}, status=401)
    
    if event_name == 'message':
        message_data = event_data.get('message', {})
        
        message_type = message_data.get('type')
        message_sender_id = message_data.get('from', '')
        message_sender_phone_number = message_sender_id.replace('@c.us', '')
        
        if message_type == 'chat':
            message_created_at = datetime.fromtimestamp(int(message_data.get('timestamp', 0)))
            message_content = message_data.get('body', '')

            print(f"Received message from {message_sender_phone_number} at {message_created_at}: {message_content}")
            process_next_step_for_order.delay(
                message_sender_phone_number, 
                instance_id, 
                message_content,
                message_type=message_type
            )
        
        elif message_type == "ptt":
            media = event_data.get('media', {})
            media_type = media.get('mimetype', '')
            media_data = media.get('data', '')
            
            # Pass all necessary information to the task
            process_next_step_for_order.delay(
                message_sender_phone_number,
                instance_id,
                '',  # No text content for audio
                message_type=message_type,
                media_type=media_type,
                media_data=media_data
            )
            
        return JsonResponse({'status': 'success'})
    else:
        return JsonResponse({'error': 'Event not supported'}, status=404)
