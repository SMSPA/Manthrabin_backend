from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    ConversationViewSet,
    # ConversationSearchView,
    PromptsListView,
    PromptCreateView,
    PromptsSearchView
    )


router = DefaultRouter()
router.register(r'', ConversationViewSet, basename='conversation')

urlpatterns = [
    *router.urls,
    path('<uuid:conversation_id>/prompts/',
         PromptsListView.as_view(),
         name='conversation-prompts-list'),
    path('<uuid:conversation_id>/prompts/create/',
         PromptCreateView.as_view(),
         name='prompt-create'),

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
