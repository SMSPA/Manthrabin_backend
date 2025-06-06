import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
import asyncio

from rag_utils.chat_util import simple_chat
from rag_utils.conversation_name import chat_name
from conversations.models import Conversation,Prompt


class ChatConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.conversation=None
        self.first_time = False

    async def connect(self):
        user = self.scope.get('user', None)

        if not user.is_authenticated:
            print("Oh No")
            await self.close(code=4001)
            return
        conversation_public_id= self.scope['url_route']['kwargs']['conversation_public_id']
        self.conversation, prompt_count = await self.is_valid_conversation(user, conversation_public_id)
        if self.conversation is None:
            print("invalid conversation")
            await self.close(code=4003)
            return
        if prompt_count == 0:
            self.first_time = True
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

            prompt = await self.save_message(full_response_for_db, text_data)
            if self.first_time and prompt is not None:
                self.first_time = False
                history = self.create_history([prompt])
                new_title = chat_name(history)
                await self.update_conversation(new_title)



    @database_sync_to_async
    def is_valid_conversation(self, user, conversation_public_id):
        try:
            conversation=Conversation.objects.get(public_id=conversation_public_id, user=user)
            return conversation, conversation.prompts.all().count()
        except Conversation.DoesNotExist:
            return None

    def get_chunks(self,prompt):
        return simple_chat(prompt, sessionID=self.scope['conversation_publicId'])

    @database_sync_to_async
    def save_message(self, response, text):
        created_prompt = Prompt.objects.create(
            user_prompt=text,
            response=response,
            conversation=self.conversation,
        )
        return created_prompt
    @database_sync_to_async
    def update_conversation(self, title):
        self.conversation.title = title
        self.conversation.save()

    def create_history(self, prompts):
        history =[]
        for prompt in prompts:
            new_history= [
                {"Role": "user", "Message": prompt.user_prompt},
                {"Role": "assistant", "Message": prompt.response},
            ]
            history.extend(new_history)
        return history
