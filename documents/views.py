from rest_framework import viewsets, permissions, parsers, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import FileResponse
from django.core.exceptions import ValidationError
import logging # TODO: improve usage of logging 
from .models import Document
from .serializers import DocumentSerializer
# TODO: add docker-compose then uncomment this line
from rag_utils.elastic import add_docs_pipeline, delete_docs_pipeline, es_client


class AdminOnlyPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        print(request.user.AccountType)
        return request.user and hasattr(request.user, 'AccountType') and request.user.AccountType == 'Admin'


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [AdminOnlyPermission]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]
    lookup_field = 'public_id'

    logger = logging.getLogger(__name__)

    def perform_create(self, serializer: DocumentSerializer):
        if not serializer.validated_data.get('file'):
            return Response({"error": "File format is not valid."},
                            status=status.HTTP_400_BAD_REQUEST)
        self.logger.info("Creating a new document.")
        document = serializer.save()
        file_path = document.file.path
        file_public_id = str(document.public_id)
        try:
            add_docs_pipeline(file_path, file_public_id)
        except Exception as e:
            self.logger.error(f"Failed to add document to Elasticsearch: {e}", exc_info=True)
            document.delete()
            self.logger.warning(f"Deleting document with public ID {document.public_id} due to Elasticsearch failure.")
            raise serializers.ValidationError({"error": "Failed to add document to Elasticsearch."})
        

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def download(self, request, public_id=None):
        try:
            document = self.get_object()
            self.logger.warning(f"Downloading document with public ID {document.public_id}.")
            if not document.file:
                return Response({"error": "No file associated with this document."},
                                 status=status.HTTP_404_NOT_FOUND)
            
            response = FileResponse(
                document.file,
                as_attachment=True,
                filename=document.file.name.split('/')[-1]
            )
            response['Content-Length'] = document.file.size
            return response
        except Document.DoesNotExist:
            return Response({"error": "Document not found."}, 
                            status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            self.logger.error(f"Failed to download document: {e}", exc_info=True)
            raise serializers.ValidationError({"error": "Failed to download document."})


    @action(detail=True, methods=['get'], url_path='info')
    def get_document_info(self, request, public_id=None):
        document = self.get_object()
        serializer = self.get_serializer(document)
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        self.permission_classes = [permissions.IsAuthenticated]
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        self.permission_classes = [permissions.IsAuthenticated]
        return super().retrieve(request, *args, **kwargs)

    def perform_destroy(self, instance):
        self.logger.warning(f"Deleting document with public ID {instance.public_id}.")
        try:
            delete_docs_pipeline(str(instance.public_id))
        except Exception as e:
            self.logger.error(f"Failed to delete document from elastic database: {e}")
            return Response({"error": "Failed to delete document from elastic database."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
