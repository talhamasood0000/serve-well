from django.urls import path

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from backend.views import whatsapp_webhook, natural_language_query

urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('webhooks/whatsapp/<str:security_token>/', whatsapp_webhook),
    path('generate_sql/', natural_language_query, name='generate_sql'),
]
