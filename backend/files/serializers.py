import math
from rest_framework import serializers
from .models import UploadSession, FileRecord


class UploadInitSerializer(serializers.Serializer):
    filename = serializers.CharField(max_length=255)
    total_chunks = serializers.IntegerField(min_value=1)
    file_size = serializers.IntegerField(min_value=1)
    content_type = serializers.CharField(max_length=100)

    def validate_file_size(self, value):
        max_size = 100 * 1024 * 1024 * 1024  # 100GB
        if value > max_size:
            raise serializers.ValidationError('File size exceeds limit')
        return value

    def create(self, validated_data):
        file_size = validated_data['file_size']
        chunk_size = self.calculate_chunk_size(file_size)

        expected_chunks = math.ceil(file_size / chunk_size)
        if validated_data['total_chunks'] != expected_chunks:
            raise serializers.ValidationError({
                'total_chunks': f'Chunk count mismatch. Expected {expected_chunks}, got {validated_data["total_chunks"]}'
            })

        session = UploadSession.objects.create(
            filename=validated_data['filename'],
            total_chunks=validated_data['total_chunks'],
            file_size=validated_data['file_size'],
            content_type=validated_data['content_type'],
            chunk_size=chunk_size
        )
        return session

    @staticmethod
    def calculate_chunk_size(file_size):
        if file_size < 100 * 1024 * 1024:  # < 100MB
            return 5 * 1024 * 1024  # 5MB
        elif file_size < 1024 * 1024 * 1024:  # < 1GB
            return 10 * 1024 * 1024  # 10MB
        else:
            return 20 * 1024 * 1024  # 20MB


class UploadStatusSerializer(serializers.Serializer):
    uploaded_chunks = serializers.ListField(child=serializers.IntegerField())
    completed = serializers.BooleanField()
    expired = serializers.BooleanField()
    chunk_size = serializers.IntegerField()


class FileRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileRecord
        fields = ['file_id', 'filename', 'file_size', 'content_type', 'download_count', 'created_at']
