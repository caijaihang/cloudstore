from django.urls import path
from .views import (
    UploadInitView,
    UploadChunkView,
    UploadCompleteView,
    UploadStatusView,
    FileListView,
    FileDetailView,
    FileDownloadView,
)

urlpatterns = [
    path('upload/init/', UploadInitView.as_view(), name='upload-init'),
    path('upload/chunk/', UploadChunkView.as_view(), name='upload-chunk'),
    path('upload/complete/', UploadCompleteView.as_view(), name='upload-complete'),
    path('upload/status/<uuid:upload_id>/', UploadStatusView.as_view(), name='upload-status'),
    path('files/', FileListView.as_view(), name='file-list'),
    path('files/<str:file_id>/', FileDetailView.as_view(), name='file-detail'),
    path('download/<str:file_id>/', FileDownloadView.as_view(), name='file-download'),
]
