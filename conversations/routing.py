from django.urls import re_path,path
from .websocket import consumers

websocket_urlpatterns = [
    path('chat/<str:conversation_public_id>/', consumers.ChatConsumer.as_asgi()),
]