import os
from django.dispatch import receiver
from django.db.models.signals import post_delete
from django.conf import settings
from .models import ChunkUpload, FileRecord


@receiver(post_delete, sender=ChunkUpload)
def delete_chunk_file(sender, instance, **kwargs):
    """Delete physical chunk file when ChunkUpload record is deleted."""
    try:
        if instance.chunk_path:
            full_path = os.path.join(settings.MEDIA_ROOT, instance.chunk_path)
            if os.path.exists(full_path):
                os.remove(full_path)
    except (FileNotFoundError, OSError):
        pass  # File already gone or permission issue, ignore silently


@receiver(post_delete, sender=FileRecord)
def delete_merged_file(sender, instance, **kwargs):
    """Delete physical merged file when FileRecord is deleted."""
    try:
        if instance.file_path:
            full_path = os.path.join(settings.MEDIA_ROOT, instance.file_path)
            if os.path.exists(full_path):
                os.remove(full_path)
    except (FileNotFoundError, OSError):
        pass
