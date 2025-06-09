import uuid

from django.test import TestCase
from django.utils import timezone


from conversations.models import LLMModel, Conversation, Prompt, SharedConversation
from users.models import User


class LLMModelTestCase(TestCase):

    def test_create_llm_model(self):
        model_name = "GPT-3"
        llm_model = LLMModel.objects.create(name=model_name)
        self.assertEqual(llm_model.name, model_name)
        self.assertIsNotNone(llm_model.public_id)
        self.assertTrue(isinstance(llm_model.public_id, uuid.UUID))

    def test_unique_public_id(self):
        llm_model_1 = LLMModel.objects.create(name="GPT-2")
        llm_model_2 = LLMModel.objects.create(name="GPT-3")
        self.assertNotEqual(llm_model_1.public_id, llm_model_2.public_id)


class ConversationTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(email="testuser@example.com", password="password123", first_name = "test", last_name = "user" )
        self.llm_model = LLMModel.objects.create(name="GPT-4")

    def test_create_conversation(self):
        conversation = Conversation.objects.create(user=self.user, model=self.llm_model, title="Test Conversation")
        self.assertEqual(conversation.title, "Test Conversation")
        self.assertEqual(conversation.user, self.user)
        self.assertEqual(conversation.model, self.llm_model)
        self.assertIsNotNone(conversation.public_id)
        self.assertTrue(isinstance(conversation.public_id, uuid.UUID))

    def test_conversation_timestamps(self):
        conversation = Conversation.objects.create(user=self.user, model=self.llm_model, title="Time Test")
        now = timezone.now()
        self.assertTrue(now - conversation.created_at < timezone.timedelta(seconds=5))
        self.assertTrue(now - conversation.updated_at < timezone.timedelta(seconds=5))

    def test_foreign_key_integrity(self):
        conversation = Conversation.objects.create(user=self.user, model=self.llm_model, title="Test ForeignKey")
        self.assertEqual(conversation.user.email, self.user.email)
        self.assertEqual(conversation.model.name, self.llm_model.name)


class PromptTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(email="testuser@example.com", password="password123", first_name = "test", last_name = "user" )
        self.llm_model = LLMModel.objects.create(name="BERT")
        self.conversation = Conversation.objects.create(user=self.user, model=self.llm_model, title="Conversation 1")

    def test_create_prompt(self):
        prompt_text = "What is AI?"
        response_text = "AI is Artificial Intelligence."
        prompt = Prompt.objects.create(user_prompt=prompt_text, response=response_text, conversation=self.conversation)

        self.assertEqual(prompt.user_prompt, prompt_text)
        self.assertEqual(prompt.response, response_text)
        self.assertEqual(prompt.conversation, self.conversation)
        self.assertIsNotNone(prompt.public_id)
        self.assertTrue(isinstance(prompt.public_id, uuid.UUID))

    def test_prompt_ordering(self):
        prompt_1 = Prompt.objects.create(user_prompt="Prompt 1", response="Response 1", conversation=self.conversation)
        prompt_2 = Prompt.objects.create(user_prompt="Prompt 2", response="Response 2", conversation=self.conversation)

        prompts = Prompt.objects.all()
        self.assertEqual(prompts[0], prompt_2)  # Should be ordered by `time` in descending order


class SharedConversationTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(email="testuser@example.com", password="password123", first_name = "test", last_name = "user" )
        self.llm_model = LLMModel.objects.create(name="T5")
        self.conversation = Conversation.objects.create(user=self.user, model=self.llm_model,
                                                        title="Shared Conversation")
        self.prompt = Prompt.objects.create(user_prompt="Prompt for shared", response="Response for shared",
                                            conversation=self.conversation)

    def test_create_shared_conversation(self):
        shared_conversation = SharedConversation.objects.create(last_prompt=self.prompt, conversation=self.conversation)
        self.assertEqual(shared_conversation.conversation, self.conversation)
        self.assertEqual(shared_conversation.last_prompt, self.prompt)
        self.assertIsNotNone(shared_conversation.public_id)
        self.assertTrue(isinstance(shared_conversation.public_id, uuid.UUID))

    def test_shared_conversation_foreign_key_integrity(self):
        shared_conversation = SharedConversation.objects.create(last_prompt=self.prompt, conversation=self.conversation)
        self.assertEqual(shared_conversation.conversation.title, self.conversation.title)
        self.assertEqual(shared_conversation.last_prompt.user_prompt, self.prompt.user_prompt)

    def test_shared_conversation_creation_time(self):
        shared_conversation = SharedConversation.objects.create(last_prompt=self.prompt, conversation=self.conversation)
        now = timezone.now()
        self.assertTrue(now - shared_conversation.created_at < timezone.timedelta(seconds=1))

