import json

from Demos.FileSecurityTest import permissions
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from pyasn1.debug import scope
import asyncio

from .rag_util import simple_chat
from conversations.models import Conversation


class ChatConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.conversation_public_id = None

    async def connect(self):
        user_id = self.scope.get('user_id', None)

        if 'error' in self.scope:
            await self.close(code=4001)

        self.conversation_public_id = self.scope['url_route']['kwargs']['conversation_public_id']

        if user_id is None:
            print("invalid user_id")
            await self.close(code=4001)
            return

        if not await self.is_valid_conversation(user_id, self.conversation_public_id):
            print("invalid conversation")
            await self.close(code=4003)
            return

        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        print("received", text_data)
        if text_data:
            gen = await asyncio.to_thread(simple_chat, text_data, self.conversation_public_id)
            for chunk in gen:
                await self.send(text_data=chunk)

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
            Conversation.objects.get(public_id=conversation_public_id, user_id=user_id)
            return True
        except Conversation.DoesNotExist:
            return False
    def get_chunks(self,prompt):
        return simple_chat(prompt, sessionID=self.conversation_public_id)