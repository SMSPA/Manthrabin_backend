import uuid
from smtplib import SMTPException
from uuid import uuid4

from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, status, viewsets
from haystack.query import SearchQuerySet
from django.db.models import Q

from manthrabin_backend import settings
from .models import Conversation, Prompt, SharedConversation
from .serializers import ConversationSerializer, PromptSerializer
from documents.views import AdminOnlyPermission
from rest_framework.pagination import LimitOffsetPagination
from .websocket.rag_util import simple_chat

class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'public_id'
    pagination_class = LimitOffsetPagination

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        return Conversation.objects.filter(user=self.request.user)


class PromptsListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PromptSerializer
    pagination_class = LimitOffsetPagination

    def get_queryset(self):
        conversation_id = self.kwargs['conversation_id']
        conversation = get_object_or_404(Conversation, public_id=conversation_id, user=self.request.user)
        return Prompt.objects.filter(conversation=conversation)


class PromptCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PromptSerializer

    def perform_create(self, serializer):
        conversation_id = self.kwargs['conversation_id']
        conversation = get_object_or_404(Conversation, public_id=conversation_id, user=self.request.user)

        if conversation.user != self.request.user:
            raise PermissionDenied("invalid conversation.")
            prompt = serializer.validated_data.get('user_prompt')
            response = simple_chat(prompt, conversation.public_id)
            serializer.save(conversation=conversation, response=response)

class CreateConversationLinkView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, **kwargs):
        conversation_public_id= kwargs.get('conversation_id')
        conversation = get_object_or_404(Conversation, public_id=conversation_public_id)
        if conversation.user != self.request.user:
            raise PermissionDenied("invalid conversation.")
        share_link = self._create_or_update_shared_conversation(conversation)
        return Response(
            {
                "share_link": str(share_link.public_id),
                "conversation_id": str(conversation.public_id),
            },
            status=200)

    def post(self, request, **kwargs):
        email = request.data.get('email')
        conversation_public_id = kwargs.get('conversation_id')
        conversation = get_object_or_404(Conversation, public_id=conversation_public_id)
        if conversation.user != self.request.user:
            raise PermissionDenied("invalid conversation.")
        share_link =  self._create_or_update_shared_conversation( conversation)
        link=f"127.0.0.1:3000/share_conversation/{share_link.public_id}"

        try:
            send_mail(
                subject= f"Manthrabin Shared Conversation",
                message=f"Click the link below to access conversation :\n{link}",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[email],
                fail_silently=False,

            )
        except SMTPException as e:
            return Response(
                {"error": "Failed to send email.", "details": str(e)},
                status=502
            )

        return Response({
            "message": f"Share link sent to {email}."
        }, status=200)

    def _create_or_update_shared_conversation(self, conversation):
        last_prompt = conversation.prompts.first()
        try:
            share_link = SharedConversation.objects.get(conversation=conversation)
            if share_link.last_prompt != last_prompt:
                share_link.last_prompt = last_prompt
                share_link.public_id = uuid.uuid4()
                share_link.save()
        except SharedConversation.DoesNotExist:
            share_link = SharedConversation.objects.create(
                conversation=conversation,
                last_prompt=last_prompt,
            )
            share_link.save()
        return share_link



class ShareConversationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, **kwargs):
        shared_conversation = get_object_or_404(SharedConversation, public_id=kwargs.get('share_id'))
        original_conversation = shared_conversation.conversation
        new_conversation = Conversation.objects.create(
            user=request.user,
            model= original_conversation.model,
            title = original_conversation.title
        )
        prompts_to_copy = Prompt.objects.filter(
            conversation=original_conversation,
            time__lte=shared_conversation.last_prompt.time
        )

        new_prompts = []
        for prompt in prompts_to_copy:
            new_prompts.append(Prompt(
                conversation=new_conversation,
                user_prompt=prompt.user_prompt,
                response=prompt.response,
                ))
        Prompt.objects.bulk_create(new_prompts)

        copied_prompts_qs = Prompt.objects.filter(conversation=new_conversation)
        paginator = LimitOffsetPagination()
        paginated = paginator.paginate_queryset(copied_prompts_qs, request)
        serializer = PromptSerializer(paginated, many=True)
        return paginator.get_paginated_response(serializer.data)




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
