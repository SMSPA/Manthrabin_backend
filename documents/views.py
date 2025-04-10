from rest_framework import viewsets, permissions, parsers, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import FileResponse
import logging
from .models import Document
from .serializers import DocumentSerializer


class AdminOnlyPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        print(request.user.AccountType)
        return request.user and hasattr(request.user, 'AccountType') and request.user.AccountType == 'Admin'


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAdminUser]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    logger = logging.getLogger(__name__)

    def perform_create(self, serializer):
        if not serializer.validated_data.get('file'):
            raise serializers.ValidationError({"file": "File is required."})
        self.logger.info("Creating a new document.")
        serializer.save()

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def download(self, request, pk=None):
        document = self.get_object()
        try:
            with document.file.open() as file:
                return FileResponse(
                    file,
                    as_attachment=True,
                    filename=document.file.name.split('/')[-1]
                )
        except FileNotFoundError:
            return Response({"error": "File not found."}, status=404)

    @action(detail=True, methods=['get'], url_path='info')
    def get_document_info(self, request, pk=None):
        document = self.get_object()
        serializer = self.get_serializer(document)
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        self.permission_classes = [permissions.IsAuthenticated]
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        self.permission_classes = [permissions.IsAuthenticated]
        return super().retrieve(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.logger.warning(f"Deleting document with ID {instance.id}.")
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
