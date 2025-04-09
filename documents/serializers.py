from rest_framework import serializers
from .models import Document


class DocumentSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    file_name = serializers.SerializerMethodField()
    file_size = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = ['id', 'title', 'file', 'file_url', 'file_name', 'file_size', 'created_at', 'updated_at']
        read_only_fields = ['file_url', 'file_name', 'file_size', 'created_at', 'updated_at']

    def get_file_url(self, obj):
        return self.context['request'].build_absolute_uri(obj.file.url)

    def get_file_name(self, obj):
        return obj.file.name.split('/')[-1]

    def get_file_size(self, obj):
        return obj.file.size
