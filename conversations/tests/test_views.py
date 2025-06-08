from smtplib import SMTPException

from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from django.contrib.auth import get_user_model
from django.urls import reverse
from uuid import uuid4
from conversations.models import Conversation, Prompt, SharedConversation, LLMModel
from django.core.mail import send_mail
from unittest.mock import patch
from django.core.exceptions import ValidationError
import smtplib


class APIViewsTestCase(APITestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="user@example.com", password="password123", first_name = "test", last_name = "user"
        )
        self.llm_model = LLMModel.objects.create(name="GPT-4")
        self.conversation = Conversation.objects.create(
            user=self.user, model=self.llm_model, title="Test Conversation"
        )
        self.prompt = Prompt.objects.create(
            user_prompt="What is AI?", response="Artificial Intelligence.", conversation=self.conversation
        )
        self.client.force_authenticate(user=self.user)

    def test_unauthenticated_access(self):
        self.client.force_authenticate(user=None)
        url = reverse('conversation-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_conversation_view_set_create(self):
        url = reverse('conversation-list')
        data = {
            "model": self.llm_model.public_id,
            "title": "New Conversation"
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], "New Conversation")
        self.assertEqual(response.data['model_info']['name'], self.llm_model.name)

    def test_conversation_view_set_permissions(self):
        other_user = get_user_model().objects.create_user(
            email="otheruser@example.com", password="password123", first_name = "user", last_name = "test"
        )
        self.client.force_authenticate(user=other_user)
        url = reverse('conversation-detail', kwargs={'public_id': self.conversation.public_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # def test_prompt_create(self):
    #     url = reverse('prompt-create', kwargs={'conversation_id': self.conversation.public_id})
    #     data = {
    #         "user_prompt": "What is the capital of France?"
    #     }
    #     response = self.client.post(url, data)
    #     self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    #     self.assertEqual(response.data['user_prompt'], "What is the capital of France?")
    #     self.assertIsNotNone(response.data['response'])
    #
    # def test_invalid_prompt_create(self):
    #     url = reverse('prompt-create', kwargs={'conversation_id': self.conversation.public_id})
    #     data = {"user_prompt": ""}
    #     response = self.client.post(url, data)
    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_conversation_link(self):
        url = reverse('share-conversation', kwargs={'conversation_id': self.conversation.public_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("share_link", response.data)

    def test_create_conversation_link_mismatched_user(self):
        other_user = get_user_model().objects.create_user(
            email="otheruser@example.com", password="password123", first_name = "user", last_name = "test"
        )
        self.client.force_authenticate(user=other_user)
        url = reverse('share-conversation', kwargs={'conversation_id': self.conversation.public_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch('django.core.mail.send_mail')
    def test_send_share_conversation_email(self, mock_send_mail):
        """Test the functionality of sharing the conversation via email"""
        mock_send_mail.return_value = True
        url = reverse('share-conversation', kwargs={'conversation_id': self.conversation.public_id})
        data = {'email': 'test@example.com'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Share link sent to test@example.com.", response.data['message'])


    def test_share_conversation(self):
        shared_conversation = SharedConversation.objects.create(
            conversation=self.conversation, last_prompt=self.prompt
        )
        url = reverse('share-conversation', kwargs={'share_id': shared_conversation.public_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
    #
    # def test_conversation_search(self):
    #     url = reverse('conversation-search', kwargs={'conversation_id': self.conversation.public_id})
    #     response = self.client.get(url, {"q": "AI"})
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     self.assertGreater(len(response.data), 0)

    def test_conversation_search_missing_query(self):
        url = reverse('conversation-search')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_prompt_search(self):
        url = reverse('prompts-search', kwargs={'conversation_id': self.conversation.public_id})
        response = self.client.get(url, {"q": "AI"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)

    def test_invalid_prompt_search(self):
        url = reverse('prompts-search', kwargs={'conversation_id': self.conversation.public_id})
        with self.assertRaises(ValidationError):
             self.client.get(url)

