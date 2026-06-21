from django.urls import path, include, re_path
from . import views

urlpatterns = [
    # 1. API 接口优先匹配
    path('api/', include('files.urls')),

    # 2. 用户上传文件的访问路径
    re_path(r'^media/(?P<path>.*)$', views.serve_media, name='media'),

    # 3. 首页
    path('', views.index, name='index'),

    # 4. 其他所有路径：先尝试服务静态文件，不存在则回退到 index.html
    #    这样 Vue Router 的 history 模式（/upload、/manage、/help 等）能正常工作
    re_path(r'^(?P<path>.+)$', views.serve_frontend_or_index),
]
