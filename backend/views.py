import base64
import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import datetime

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from backend.models import Company
from backend.tasks import process_next_step_for_order
from backend.agent import SQLGeneratorAgent


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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def natural_language_query(request):
    """
    API endpoint that accepts a natural language query and returns:
    - Data from a DataFrame as a dictionary
    - A visualization of the data as a base64 encoded image
    """
    
    try:
        body = json.loads(request.body)
        query = body.get('query')
        
        if not query:
            return JsonResponse({'error': 'No query provided'}, status=400)
        
        sql_agent = SQLGeneratorAgent()
        df, image_base64 = sql_agent.run_pipeline(query) 
        
        # Convert DataFrame to dictionary
        data_dict = df.to_dict(orient='records')
        
        return JsonResponse({
            'status': 'success',
            'data': data_dict,
            'sql_query': sql_agent.sql_query,
            'visualization': image_base64,
            'metadata': {
                'columns': list(df.columns),
                'shape': df.shape,
                'query': query
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
