from rest_framework import viewsets, permissions, parsers, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import FileResponse
import logging # TODO: improve usage of logging 
from .models import Document
from .serializers import DocumentSerializer
# TODO: add docker-compose then uncomment this line
# from .elastic import add_docs_pipeline, delete_docs_pipeline, es_client


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

    def perform_create(self, serializer):
        if not serializer.validated_data.get('file'):
            raise serializers.ValidationError({"file": "File is required."})
        self.logger.info("Creating a new document.")
        document = serializer.save()
        file_path = document.file.path
        # add_docs_pipeline(file_path)

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def download(self, request, public_id=None):
        try:
            document = self.get_object()
            if not document.file:
                return Response({"error": "No file associated with this document."}, status=404)
            
            response = FileResponse(
                document.file,
                as_attachment=True,
                filename=document.file.name.split('/')[-1]
            )
            response['Content-Length'] = document.file.size
            return response
        except Document.DoesNotExist:
            return Response({"error": "Document not found."}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=500)


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

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except Document.DoesNotExist:
            return Response({"error": "Document not found."}, status=status.HTTP_404_NOT_FOUND)

        self.logger.warning(f"Deleting document with public ID {instance.public_id}.")

        # try:
        #     index_name = "manthrabin"
        #     query_body = {
        #         "query": {
        #             "term": {"uuid": instance.public_id}
        #         },
        #         "_source": ["uuid"]
        #     }
        #     response = es_client.search(index=index_name, body=query_body)
        #     uuids = [hit['_source']['uuid'] for hit in response['hits']['hits']]

        #     delete_docs_pipeline(uuids)
        # except Exception as e:
        #     self.logger.error(f"Failed to delete document from elastic database: {e}")
        #     return Response({"error": "Failed to delete document from elastic database."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        instance.file.delete(save=False)
        instance.delete()

        return Response({"message": "Document deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
