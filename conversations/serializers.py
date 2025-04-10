from rest_framework import serializers
from .models import Conversation


class ConversationsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = "__all__"
