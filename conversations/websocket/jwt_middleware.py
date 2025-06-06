from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from channels.db import database_sync_to_async

from users.models import User

from urllib.parse import parse_qs


class JWTAuthMiddleware(BaseMiddleware):

    async def __call__(self, scope, receive, send):
        token = self.get_token_from_scope(scope)
        if token is None:
            scope['user']=AnonymousUser()
        else:
            user = await self.get_user_from_token(token)
            scope['user']=user

        return await super().__call__(scope, receive, send)

    def get_token_from_scope(self, scope):
        headers = dict(scope.get("headers", []))
        auth_header = headers.get(b'authorization')

        if auth_header:
            try:
                auth_header = auth_header.decode('utf-8')
            except UnicodeDecodeError:
                return None
            if auth_header.startswith('Bearer '):
                return auth_header.split(' ')[1]

        # Fallback to check query string
        query_string = scope.get('query_string', b'').decode('utf-8')
        params = dict(qc.split("=") for qc in query_string.split("&") if "=" in qc)
        token = params.get('token')
        if token:
            return token

        return None

    @database_sync_to_async
    def get_user_from_token(self, token):
        try:
            access_token = AccessToken(token)
            user_id = access_token["user_id"]
            return User.objects.get(id=user_id)
        except Exception:
            return AnonymousUser()