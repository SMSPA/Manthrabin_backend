from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    ConversationViewSet,
    ConversationSearchView,
    PromptsListView,
    PromptCreateView,
    PromptsSearchView, CreateConversationLinkView, ShareConversationView
)


router = DefaultRouter()
router.register(r'', ConversationViewSet, basename='conversation')

urlpatterns = [
    path(
        'search/',
        ConversationSearchView.as_view(),
        name='conversation-search'
    ),
    *router.urls,
    path('<uuid:conversation_id>/prompts/',
         PromptsListView.as_view(),
         name='conversation-prompts-list'),
    path('<uuid:conversation_id>/prompts/create/',
         PromptCreateView.as_view(),
         name='prompt-create'),
    path('<uuid:conversation_id>/share/',
         CreateConversationLinkView.as_view(),
         name = 'share-conversation'),
path('share/<uuid:share_id>/',
         ShareConversationView.as_view(),
         name = 'share-conversation'),
    path(
        '<uuid:conversation_id>/search/', 
        PromptsSearchView.as_view(),
        name='prompts-search'
    ),
]
