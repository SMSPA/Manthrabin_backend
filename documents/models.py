import uuid
from django.db import models
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError


class Document(models.Model):
    def validate_file_size(value):
        max_size = 50 * 1024 * 1024
        if value.size > max_size:
            raise ValidationError("File size cannot exceed 10MB.")

    id = models.AutoField(primary_key=True)
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    title = models.TextField(max_length=50)
    file = models.FileField(
        upload_to='documents/',
        validators=[
            FileExtensionValidator(allowed_extensions=['pdf', 'docx', 'doc', 'txt', 'pptx', 'xlsx']),
            validate_file_size,
        ]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def delete(self, *args, **kwargs):
        self.file.delete()
        super().delete(*args, **kwargs)
