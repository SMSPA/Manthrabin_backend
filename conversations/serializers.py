from rest_framework import serializers
from .models import Conversation, Prompt, LLMModel

class LLMModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = LLMModel
        fields = ('public_id', 'name')

class PromptSerializer(serializers.ModelSerializer):
    conversation_id = serializers.CharField(source='conversation.public_id',read_only=True)

    class Meta:
        model = Prompt
        fields = ('public_id', 'user_prompt', 'response', 'time', 'conversation_id')
        read_only_fields = ('public_id','response' ,'time')


class ConversationSerializer(serializers.ModelSerializer):
    model = serializers.UUIDField(write_only=True)
    model_info = serializers.SerializerMethodField()
    title = serializers.CharField(required=False)

    class Meta:
        model = Conversation
        fields = ['public_id', 'title', 'model','model_info','created_at', 'updated_at']
        read_only_fields = ['public_id', 'created_at', 'updated_at','model_info']

    def create(self, validated_data):
        model_public_id = validated_data.pop('model')
        try:
            llm_model = LLMModel.objects.get(public_id=model_public_id)
        except LLMModel.DoesNotExist:
            raise serializers.ValidationError({"model": "Model with this public ID does not exist."})
        validated_data['user'] = self.context['request'].user
        validated_data['model']=llm_model
        return super().create(validated_data)

    def get_model_info(self, obj):
        return {
            "public_id": obj.model.public_id,
            "name": obj.model.name,
        }


class PromptMatchSerializer(serializers.Serializer):
    prompt_id = serializers.UUIDField()
    user_prompt = serializers.CharField()
    response = serializers.CharField()
    time = serializers.DateTimeField()


class ConversationSearchSerializer(serializers.Serializer):
    conversation_id = serializers.UUIDField()
    title = serializers.CharField()
    matching_prompts = PromptMatchSerializer(many=True)


class PromptSearchSerializer(serializers.Serializer):
    prompt_id = serializers.UUIDField()
