from django_elasticsearch_dsl import Document, fields, Index
from django_elasticsearch_dsl.registries import registry
from .models import Conversation, Prompt

conversation_index = Index("conversations")
conversation_index.settings(
    number_of_shards=1,
    number_of_replicas=0
)

prompt_index = Index("prompts")
prompt_index.settings(
    number_of_shards=1,
    number_of_replicas=0
)


@conversation_index.document
class ConversationDocument(Document):
    """
    Elasticsearch “document” mapping for Conversation.
    We index fields we want to query/filter on.
    """
    public_id = fields.KeywordField()
    title     = fields.TextField()
    user_id   = fields.IntegerField(attr="user_id")

    class Index:
        name = "conversations"

    class Django:
        model = Conversation

    def get_queryset(self):
        # only index active/published items (optional)
        return super().get_queryset().all()


@prompt_index.document
class PromptDocument(Document):
    """
    Elasticsearch “document” mapping for Prompt.
    We index both user_prompt and response, plus the parent conversation’s UUID & user_id.
    """
    public_id            = fields.KeywordField()        
    user_prompt          = fields.TextField()          
    response             = fields.TextField()          
    conversation_public_id = fields.KeywordField(attr="conversation.public_id")
    user_id              = fields.IntegerField(attr="conversation.user_id")
    time                 = fields.DateField()

    class Index:
        name = "prompts"

    class Django:
        model = Prompt

    def get_queryset(self):
        return super().get_queryset().select_related("conversation")