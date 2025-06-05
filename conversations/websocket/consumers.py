import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
import asyncio

from .rag_util import simple_chat
from conversations.models import Conversation,Prompt


class ChatConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.conversation=None

    async def connect(self):
        user = self.scope.get('user', None)

        if not user.is_authenticated:
            print("Oh No")
            await self.close(code=4001)
            return
        conversation_public_id= self.scope['url_route']['kwargs']['conversation_public_id']
        self.conversation = await self.is_valid_conversation(user, conversation_public_id)
        if self.conversation is None:
            print("invalid conversation")
            await self.close(code=4003)
            return

        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        print("received", text_data)
        if text_data:
            gen = await asyncio.to_thread(simple_chat, text_data, self.conversation.public_id)
            full_response_for_db = ""
            for chunk in gen:
                full_response_for_db += chunk
                await self.send(text_data=chunk) # Send data chunk

            # After sending all data chunks, send an end-of-stream signal
            await self.send(text_data=json.dumps({"type": "stream_end", "conversation_id": str(self.conversation.public_id)}))
            print(f"Sent stream_end signal for conversation {self.conversation.public_id}")

            await self.save_message(full_response_for_db, text_data)

    @database_sync_to_async
    def is_valid_conversation(self, user, conversation_public_id):
        try:
            conversation=Conversation.objects.get(public_id=conversation_public_id, user=user)
            return conversation
        except Conversation.DoesNotExist:
            return None
    def get_chunks(self,prompt):
        return simple_chat(prompt, sessionID=self.scope['conversation_publicId'])

    @database_sync_to_async
    def save_message(self, response, text):
        return Prompt.objects.create(
            user_prompt=text,
            response=response,
            conversation=self.conversation,

        )
