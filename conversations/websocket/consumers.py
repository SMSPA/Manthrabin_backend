import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
import asyncio

from rag_utils.chat_util import simple_chat
from rag_utils.conversation_name import chat_name
from conversations.models import Conversation, Prompt
from rag_utils.response_pipeline import stream
from users.models import UserInterest


class ChatConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.conversation = None
        self.prompts = None
        self.model_name = ""
        self.user_interests = None
        self.first_time = False

    async def connect(self):
        user = self.scope.get('user', None)

        if not user.is_authenticated:
            print("Oh No")
            await self.close(code=4001)
            return

        conversation_public_id = self.scope['url_route']['kwargs']['conversation_public_id']
        self.conversation, self.model_name = await self.is_valid_conversation(user, conversation_public_id)
        self.prompts = await self.conversation_prompts()
        self.user_interests = await self.get_users_interests(user)
        if self.conversation is None:
            print("invalid conversation")
            await self.close(code=4003)
            return

        if len(self.prompts) == 0:
            self.first_time = True
        await self.accept()

    async def disconnect(self, close_code):
        await self.close(code=close_code)

    async def receive(self, text_data):
        print("received", text_data)
        if text_data:
            history = self.create_history(self.prompts[-10:])
            full_response_for_db = ""
            for response in stream(query=text_data, history=history, favorites=self.user_interests,
                                   model_name=self.conversation.model.name):
                if response["type"] == "chunk":
                    full_response_for_db += response["response"]
                    await self.send(response["response"])
                if response["type"] == "source":
                    await self.send(
                        text_data=json.dumps({"type": "source", "conversation_id": str(self.conversation.public_id)}))
                    for source in response["sourcePoints"]:
                        await self.send(
                            text_data = json.dumps({"public_id": source['ID'], "context": source['context']}))
                    await self.send(
                        text_data=json.dumps({"type": "link", "conversation_id": str(self.conversation.public_id)}))
                    for link in response["links_data"]:
                        await self.send(
                            text_data=json.dumps({"link": link['Link']}))

            # After sending all data chunks, send an end-of-stream signal
            await self.send(
                text_data=json.dumps({"type": "stream_end", "conversation_id": str(self.conversation.public_id)}))
            print(f"Sent stream_end signal for conversation {self.conversation.public_id}")

            prompt = await self.save_message(full_response_for_db, text_data)
            self.prompts.append(prompt)

            if self.first_time and prompt is not None:
                self.first_time = False
                history = self.create_history([prompt])
                new_title = chat_name(history = history )
                await self.update_conversation(new_title)

    @database_sync_to_async
    def is_valid_conversation(self, user, conversation_public_id):
        try:
            conversation = Conversation.objects.get(public_id=conversation_public_id, user=user)
            return conversation, conversation.model.name
        except Conversation.DoesNotExist:
            return None

    @database_sync_to_async
    def conversation_prompts(self):
        return list(self.conversation.prompts.all())

    @database_sync_to_async
    def get_users_interests(self, user):
        interests = UserInterest.objects.filter(UserID=user)
        return [interest.InterestID.Title for interest in interests]

    def get_chunks(self, prompt):
        history = self.create_history(self.prompts[-10:])
        return stream(query=prompt, history=history, favorites=self.user_interests,
                      model_name=self.conversation.model_name)

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
        history = []
        for prompt in prompts:
            new_history = [
                {"Role": "user", "Message": prompt.user_prompt},
                {"Role": "assistant", "Message": prompt.response},
            ]
            history.extend(new_history)
        return history
