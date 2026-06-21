from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from files.models import UploadSession


class Command(BaseCommand):
    help = 'Cleanup expired upload sessions (older than 7 days) and their chunk files'

    def handle(self, *args, **options):
        expired_sessions = UploadSession.objects.filter(
            is_completed=False,
            created_at__lt=timezone.now() - timedelta(days=7)
        )

        count = expired_sessions.count()

        for session in expired_sessions:
            # CASCADE deletes related ChunkUpload records
            # post_delete signal on ChunkUpload deletes physical files
            session.delete()
            self.stdout.write(f'Deleted expired session: {session.upload_id}')

        self.stdout.write(
            self.style.SUCCESS(f'Cleaned up {count} expired upload sessions')
        )
