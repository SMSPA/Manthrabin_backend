from django.db import models
from users.models import User
import uuid


class LLMModel(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(max_length=100)


class Conversation(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    title = models.CharField(max_length=255, default='new conversation')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    model = models.ForeignKey(LLMModel, on_delete=models.CASCADE)


class Prompt(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user_prompt = models.TextField()
    response = models.TextField()
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="prompts")
    time = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-time',)
