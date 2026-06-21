import uuid
from django.db import models


def generate_short_uuid():
    return uuid.uuid4().hex[:12]


class UploadSession(models.Model):
    upload_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    filename = models.CharField(max_length=255)
    total_chunks = models.IntegerField()
    file_size = models.BigIntegerField()
    content_type = models.CharField(max_length=100)
    chunk_size = models.IntegerField()
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.upload_id)


class ChunkUpload(models.Model):
    upload = models.ForeignKey(
        UploadSession,
        on_delete=models.CASCADE,
        related_name='chunks'
    )
    chunk_index = models.IntegerField()
    chunk_path = models.CharField(max_length=500)
    status = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('upload', 'chunk_index')
        ordering = ['chunk_index']

    def __str__(self):
        return f'{self.upload.upload_id}: chunk {self.chunk_index}'


class FileRecord(models.Model):
    file_id = models.CharField(
        max_length=12,
        primary_key=True,
        default=generate_short_uuid
    )
    filename = models.CharField(max_length=255)
    file_size = models.BigIntegerField()
    content_type = models.CharField(max_length=100)
    file_path = models.CharField(max_length=500)
    download_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    upload_session = models.ForeignKey(
        UploadSession,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def __str__(self):
        return self.filename
