from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework import generics, filters
from .models import Conversation
from .serializers import ConversationsSerializer


class ConversationsListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Conversation.objects.all()
    serializer_class = ConversationsSerializer
    filter_backends = [filters.SearchFilter]
    # search_fields = ['prompt', 'response']
