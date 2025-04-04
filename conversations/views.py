from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import filters, generics
from haystack.query import SearchQuerySet

from conversations.models import Conversations
from conversations.serializers import ConversationsSerializer


class SearchConversationsView(APIView):
    def get(self, request):
        query = request.GET.get("q", "")
        if query:
            results = SearchQuerySet().filter(content=query)
            conversations = [result.object for result in results if result.object]
        else:
            conversations = []

        serializer = ConversationsSerializer(conversations, many=True)
        return Response(serializer.data)


class ConversationsListView(generics.ListAPIView):
    queryset = Conversations.objects.all()
    serializer_class = ConversationsSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['prompt', 'response']


class ConversationsListCreateView(generics.ListCreateAPIView):
    queryset = Conversations.objects.all()
    serializer_class = ConversationsSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['prompt', 'response']
