import os
import math
import shutil
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import UploadSession, ChunkUpload, FileRecord
from .serializers import (
    UploadInitSerializer,
    FileRecordSerializer,
)


def get_chunk_path(upload_id, chunk_index):
    prefix = str(upload_id)[:2]
    return f'chunks/{prefix}/{upload_id}/{chunk_index}.chunk'


def get_file_path(file_id):
    prefix = file_id[:2]
    return f'files/{prefix}/{file_id}'


class UploadInitView(APIView):
    def post(self, request):
        serializer = UploadInitSerializer(data=request.data)
        if serializer.is_valid():
            session = serializer.save()
            return Response({
                'upload_id': str(session.upload_id),
                'chunk_size': session.chunk_size,
            }, status=201)
        return Response(
            {'error': serializer.errors},
            status=400
        )


class UploadChunkView(APIView):
    def post(self, request):
        upload_id = request.data.get('upload_id')
        chunk_index = request.data.get('chunk_index')
        chunk_file = request.FILES.get('chunk')

        if not all([upload_id, chunk_index is not None, chunk_file]):
            return Response(
                {'error': 'Missing required fields'},
                status=400
            )

        try:
            session = UploadSession.objects.get(upload_id=upload_id)
        except UploadSession.DoesNotExist:
            return Response(
                {'error': 'Upload session not found'},
                status=404
            )

        if session.is_completed:
            return Response(
                {'error': 'Upload already completed'},
                status=400
            )

        chunk_index = int(chunk_index)

        max_chunk_size = session.chunk_size
        if chunk_file.size > max_chunk_size:
            return Response(
                {'error': 'Chunk size exceeds limit'},
                status=400
            )

        chunk_rel_path = get_chunk_path(upload_id, chunk_index)
        full_path = os.path.join(settings.MEDIA_ROOT, chunk_rel_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        with open(full_path, 'wb') as dest:
            shutil.copyfileobj(chunk_file, dest, length=8 * 1024 * 1024)

        ChunkUpload.objects.update_or_create(
            upload=session,
            chunk_index=chunk_index,
            defaults={'chunk_path': chunk_rel_path, 'status': 'completed'}
        )

        return Response({'status': 'ok'})


class UploadCompleteView(APIView):
    def post(self, request):
        upload_id = request.data.get('upload_id')
        if not upload_id:
            return Response({'error': 'Missing upload_id'}, status=400)

        try:
            session = UploadSession.objects.select_for_update().get(upload_id=upload_id)
        except UploadSession.DoesNotExist:
            return Response(
                {'error': 'Upload session not found'},
                status=404
            )

        if session.is_completed:
            try:
                file_record = FileRecord.objects.get(upload_session=session)
                return Response({
                    'file_id': file_record.file_id,
                    'filename': file_record.filename,
                    'file_size': file_record.file_size,
                })
            except FileRecord.DoesNotExist:
                pass

        temp_path = None
        try:
            for i in range(session.total_chunks):
                chunk_rel_path = get_chunk_path(upload_id, i)
                chunk_full_path = os.path.join(settings.MEDIA_ROOT, chunk_rel_path)
                if not os.path.exists(chunk_full_path):
                    return Response(
                        {'error': f'Chunk {i} missing'},
                        status=400
                    )

            from .models import generate_short_uuid
            file_id = generate_short_uuid()
            file_rel_path = get_file_path(file_id)
            dest_full_path = os.path.join(settings.MEDIA_ROOT, file_rel_path)
            os.makedirs(os.path.dirname(dest_full_path), exist_ok=True)

            temp_path = dest_full_path + '.tmp'
            with open(temp_path, 'wb') as dest:
                for i in range(session.total_chunks):
                    chunk_rel_path = get_chunk_path(upload_id, i)
                    chunk_full_path = os.path.join(settings.MEDIA_ROOT, chunk_rel_path)
                    with open(chunk_full_path, 'rb') as src:
                        shutil.copyfileobj(src, dest, length=8 * 1024 * 1024)

            os.replace(temp_path, dest_full_path)
            temp_path = None

            with transaction.atomic():
                file_record = FileRecord.objects.create(
                    file_id=file_id,
                    filename=session.filename,
                    file_size=session.file_size,
                    content_type=session.content_type,
                    file_path=file_rel_path,
                    upload_session=session,
                )

                session.is_completed = True
                session.save()

            return Response({
                'file_id': file_record.file_id,
                'filename': file_record.filename,
                'file_size': file_record.file_size,
            })

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=500
            )
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass


class UploadStatusView(APIView):
    def get(self, request, upload_id):
        try:
            session = UploadSession.objects.get(upload_id=upload_id)
        except UploadSession.DoesNotExist:
            return Response(
                {'error': 'Upload session not found or expired'},
                status=404
            )

        expired = (timezone.now() - session.created_at) > timedelta(days=7)

        uploaded_chunks = []
        for chunk in session.chunks.filter(status='completed'):
            full_path = os.path.join(settings.MEDIA_ROOT, chunk.chunk_path)
            if os.path.exists(full_path):
                uploaded_chunks.append(chunk.chunk_index)

        return Response({
            'uploaded_chunks': sorted(uploaded_chunks),
            'completed': session.is_completed,
            'expired': expired,
            'chunk_size': session.chunk_size,
        })


class FileListView(APIView):
    def get(self, request):
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        page_size = min(page_size, 100)

        total = FileRecord.objects.count()
        files = FileRecord.objects.all().order_by('-created_at')
        files = files[(page - 1) * page_size:page * page_size]

        serializer = FileRecordSerializer(files, many=True)
        return Response({
            'total': total,
            'page': page,
            'page_size': page_size,
            'files': serializer.data,
        })


class FileDetailView(APIView):
    def get(self, request, file_id):
        try:
            file_record = FileRecord.objects.get(file_id=file_id)
        except FileRecord.DoesNotExist:
            return Response({'error': 'File not found'}, status=404)

        serializer = FileRecordSerializer(file_record)
        data = serializer.data
        data['download_url'] = f'/api/download/{file_id}/'
        return Response(data)

    def delete(self, request, file_id):
        try:
            file_record = FileRecord.objects.get(file_id=file_id)
        except FileRecord.DoesNotExist:
            return Response({'error': 'File not found'}, status=404)

        file_record.delete()
        return Response({'status': 'deleted'})


class FileDownloadView(APIView):
    def get(self, request, file_id):
        try:
            file_record = FileRecord.objects.get(file_id=file_id)
        except FileRecord.DoesNotExist:
            return Response({'error': 'File not found'}, status=404)

        FileRecord.objects.filter(file_id=file_id).update(
            download_count=F('download_count') + 1
        )

        full_path = os.path.join(settings.MEDIA_ROOT, file_record.file_path)
        if not os.path.exists(full_path):
            return Response({'error': 'File not found'}, status=404)

        from django.http import FileResponse
        response = FileResponse(open(full_path, 'rb'))
        response['Content-Disposition'] = f'attachment; filename="{file_record.filename}"'
        response['Content-Type'] = file_record.content_type
        return response
