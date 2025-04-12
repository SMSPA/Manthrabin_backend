from rest_framework import serializers
from .models import Conversation, Prompt


class ConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = "__all__"


class PromptSerializer(serializers.ModelSerializer):
    conversation_id = serializers.CharField(source='conversation.public_id')

    class Meta:
        model = Prompt
        fields = ('public_id', 'user_prompt', 'response', 'time', 'conversation_id')
        read_only_fields = ('public_id', 'time')
