"""
ASGI config for manthrabin_backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

from conversations import routing
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter

from conversations.websocket.jwt_middleware import JWTAuthMiddleware

# from your_app import consumers
application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": JWTAuthMiddleware(
        URLRouter([
            routing.websocket_urlpatterns])
    ),
})
