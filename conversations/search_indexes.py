from haystack import indexes
from .models import Prompt, Conversation


class ConversationIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    public_id = indexes.CharField(model_attr='public_id')
    title = indexes.CharField(model_attr='title')
    user_id = indexes.IntegerField(model_attr='user_id')

    def get_model(self):
        return Conversation

    def index_queryset(self, using=None):
        return self.get_model().objects.all()


class PromptIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)

    public_id = indexes.CharField(model_attr='public_id')
    user_prompt = indexes.CharField(model_attr='user_prompt')
    response = indexes.CharField(model_attr='response')
    time = indexes.DateTimeField(model_attr='time')
    conversation_public_id = indexes.CharField(model_attr='conversation.public_id')

    def get_model(self):
        return Prompt

    def index_queryset(self, using=None):
        return self.get_model().objects.all()
