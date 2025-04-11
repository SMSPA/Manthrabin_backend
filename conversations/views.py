from rest_framework import viewsets, permissions
from .models import Conversation
from .serializers import ConversationSerializer
from rest_framework.pagination import LimitOffsetPagination

class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'public_id'
    pagination_class = LimitOffsetPagination

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        return Conversation.objects.filter(user=self.request.user)