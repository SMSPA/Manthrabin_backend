from rest_framework import serializers
from .models import Document


class DocumentSerializer(serializers.ModelSerializer):
    file_path: str = serializers.SerializerMethodField()
    file_name: str = serializers.SerializerMethodField()
    file_size: int = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = ['public_id', 'title', 'file', 'file_path', 'file_name', 'file_size', 'created_at', 'updated_at']
        read_only_fields = ['public_id', 'file_path', 'file_name', 'file_size', 'created_at', 'updated_at']

    def get_file_path(self, obj: Document):
        return obj.file.path

    def get_file_name(self, obj: Document):
        return obj.file.name.split('/')[-1]

    def get_file_size(self, obj: Document):
        return obj.file.size
