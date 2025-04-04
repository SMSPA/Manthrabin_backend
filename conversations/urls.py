from django.urls import path
from .views import SearchConversationsView, ConversationsListView

urlpatterns = [
    path('', ConversationsListView.as_view()),
]
