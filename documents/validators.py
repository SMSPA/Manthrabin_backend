from os import getenv
from django.core.exceptions import ValidationError


def validate_file_size(file_obj):
    max_size = int(getenv("MAX_UPLOAD_SIZE", "10")) * 1024 * 1024
    if file_obj.size > max_size:
        raise ValidationError(f"File size cannot exceed {max_size / (1024 * 1024)} MB.")
