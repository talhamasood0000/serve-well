from django.contrib import admin
from django.urls import path, include
from backend.views import whatsapp_webhook

urlpatterns = [
    path('webhooks/whatsapp/<str:security_token>/', whatsapp_webhook),
]
