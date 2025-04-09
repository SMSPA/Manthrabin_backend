from django.db import models
from django.core.validators import FileExtensionValidator

class Document(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.TextField(max_length=50)
    file = models.FileField(
        upload_to='documents/%Y/%m/%d/',
        validators=[
            FileExtensionValidator(allowed_extensions=['pdf', 'docx', 'doc', 'txt', 'pptx', 'xlsx']),
        ]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def delete(self, *args, **kwargs):
        self.file.delete()
        super().delete(*args, **kwargs)
