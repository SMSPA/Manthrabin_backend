from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, status
from haystack.query import SearchQuerySet
from django.db.models import Q
from .models import Conversation, Prompt
from .serializers import ConversationSerializer, PromptSerializer
from documents.views import AdminOnlyPermission
from rest_framework.pagination import LimitOffsetPagination


class PromptsListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PromptSerializer
    pagination_class = LimitOffsetPagination

    def get_queryset(self):
        conversation_id = self.kwargs['conversation_id']
        conversation = get_object_or_404(Conversation, public_id=conversation_id, user=self.request.user)
        return Prompt.objects.filter(conversation=conversation)


class PromptCreateView(generics.CreateAPIView):
    permission_classes = [AdminOnlyPermission]
    serializer_class = PromptSerializer

    def perform_create(self, serializer):
        conversation_id = self.kwargs['conversation_id']
        conversation = get_object_or_404(Conversation, public_id=conversation_id, user=self.request.user)

        if conversation.user != self.request.user:
            raise PermissionDenied("You do not have permission to add a prompt to this conversation.")
        serializer.save()


class ConversationSearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        query = request.GET.get('q', '')

        if not query:
            return Response({
                "detail": "Query parameter 'q' is required."},
                status=status.HTTP_400_BAD_REQUEST,
                )
        search_results = SearchQuerySet().filter(content=query).filter(user_id=request.user.id)

        conv_results = []
        for result in search_results:
            conv = result.object

            matching_prompts = conv.prompts.filter(
                Q(user_prompt__icontains=query) | Q(response__icontains=query)
            )
            
            conv_results.append({
                "conversation_id": str(conv.public_id),
                "title": conv.title,
                "matching_prompts": [
                    {
                        "prompt_id": str(prompt.public_id),
                        "user_prompt": prompt.user_prompt,
                        "response": prompt.response,
                        "time": prompt.time,
                    } for prompt in matching_prompts
                ]
            })
        
        return Response(conv_results)


class PromptsSearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, conversation_id, format=None):
        try:
            conversation = Conversation.objects.get(public_id=conversation_id, user=request.user)
        except Conversation.DoesNotExist:
            return Response({"error": "Conversation not found."}, status=status.HTTP_404_NOT_FOUND)

        query = request.GET.get('q')
        if not query:
            return Response({"error": "Please provide a 'q' query parameter."}, status=status.HTTP_400_BAD_REQUEST)

        search_results = SearchQuerySet().filter(content=query).filter(conversation_public_id=str(conversation.public_id))

        prompts = []
        for result in search_results:
            prompt = result.object
            prompts.append({
                "prompt_id": str(prompt.public_id),
            })

        return Response(prompts)
