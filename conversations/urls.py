from django.urls import path
from .views import SearchConversationsView

urlpatterns = [
    path('search/', SearchConversationsView.as_view()),
]
