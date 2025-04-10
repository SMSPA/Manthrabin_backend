from django.urls import re_path
from .websocket import consumers

websocket_urlpatterns = [
    re_path(r"chat/(?P<conversation_publicID>\w+)/$", consumers.ChatConsumer.as_asgi()),
]