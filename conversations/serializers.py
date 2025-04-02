from rest_framework import serializers
from .models import Conversations


class ConversationsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversations
        fields = ['id', 'prompt', 'response']
