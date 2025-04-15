from django.urls import re_path,path
# QUICKFIX: UNCOMMENT when websocket is implemented
# from .websocket import consumers

# websocket_urlpatterns = [
#     path('chat/<str:conversation_public_id>/', consumers.ChatConsumer.as_asgi()),
#     # re_path(r"chat/(?P<conversation_public_id>\w+)/$", consumers.ChatConsumer.as_asgi()),
# ]