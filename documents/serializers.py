from rest_framework import serializers
from .models import Document


class DocumentSerializer(serializers.ModelSerializer):
    file_path = serializers.SerializerMethodField()
    file_name = serializers.SerializerMethodField()
    file_size = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = ['public_id', 'title', 'file', 'file_path', 'file_name', 'file_size', 'created_at', 'updated_at']
        read_only_fields = ['public_id', 'file_path', 'file_name', 'file_size', 'created_at', 'updated_at']

    def get_file_path(self, obj: Document) -> str:
        return obj.file.path

    def get_file_name(self, obj: Document) -> str:
        return obj.file.name.split('/')[-1]

    def get_file_size(self, obj: Document) -> int:
        return obj.file.size
