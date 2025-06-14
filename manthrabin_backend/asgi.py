"""
ASGI config for manthrabin_backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "manthrabin_backend.settings")

from django.core.asgi import get_asgi_application
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
from conversations.websocket.jwt_middleware import JWTAuthMiddleware
import conversations.routing

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": JWTAuthMiddleware(
        URLRouter(
            conversations.routing.websocket_urlpatterns)
    ),
})