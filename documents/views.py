from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import FileResponse
from .models import Document
from .serializers import DocumentSerializer


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        document = self.get_object()
        return FileResponse(
            document.file.open(),
            as_attachment=True,
            filename=document.file.name.split('/')[-1]
        )
