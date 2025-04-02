from rest_framework.views import APIView
from rest_framework.response import Response
from haystack.query import SearchQuerySet
from .serializers import ConversationsSerializer


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
