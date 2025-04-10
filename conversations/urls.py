from django.urls import path
from .views import ConversationsListView

urlpatterns = [
    path('', ConversationsListView.as_view()),
]
