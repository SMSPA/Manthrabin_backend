import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from conversations.models import Conversation


class ChatConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.conversation_public_id = None

    async def connect(self):
        user_id = self.scope.get('user_id', None)

        if 'error' in self.scope:
            await self.close(code=4001)

        # Get the conversation publicID from the URL path variable
        self.conversation_public_id = self.scope['url_route']['kwargs']['conversation_public_id']

        if user_id is None:
            await self.close(code=4001)
            return

        if not await self.is_valid_conversation(user_id, self.conversation_public_id):
            await self.close(code=4003)
            return

        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        prompt_data = json.loads(text_data)
        prompt = prompt_data.get('prompt').strip()

        if prompt:
            # response = await self.process_prompt(prompt)
            response= ("SOS")
            await self.send(text_data=json.dumps({
                'response': response
            }))

    @database_sync_to_async
    def is_valid_conversation(self, user_id, conversation_public_id):
        # Check if the conversation exists and belongs to the user
        try:
            Conversation.objects.get(publicID=conversation_public_id, user_id=user_id)
            return True
        except Conversation.DoesNotExist:
            return False
