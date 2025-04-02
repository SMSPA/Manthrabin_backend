import datetime
from haystack import indexes, connections
from .models import Conversations


class ConversationsIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    prompt = indexes.CharField(model_attr='prompt')
    response = indexes.CharField(model_attr='response')

    def get_model(self):
        return Conversations

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.filter(created_at__lte=datetime.datetime.now())


def update_index(instance):
    connections['default'].get_unified_index().get_index(type(instance)).update_object(instance)


def remove_from_index(instance):
    connections['default'].get_unified_index().get_index(type(instance)).remove_object(instance)
