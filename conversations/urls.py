from django.urls import path
from .views import (
    ConversationSearchView,
    PromptsListView,
    PromptCreateView,
    PromptsSearchView
    )

urlpatterns = [
    # path('', UserConversationsListView.as_view(), name='user-conversations-list'),

    path('<uuid:conversation_id>/prompts/', PromptsListView.as_view(), name='conversation-prompts-list'),
    path('<uuid:conversation_id>/prompts/create/', PromptCreateView.as_view(), name='prompt-create'),

    path(
        'search/',
        ConversationSearchView.as_view(),
        name='conversation-search'
    ),
    path(
        '<uuid:conversation_id>/search/', 
        PromptsSearchView.as_view(),
        name='prompts-search'
    ),
]
