import os
from django.http import FileResponse, HttpResponseNotFound
from django.conf import settings
from django.views.static import serve


def index(request):
    """返回前端首页 index.html"""
    index_path = os.path.join(str(settings.FRONTEND_DIR), 'index.html')
    if os.path.exists(index_path):
        return FileResponse(open(index_path, 'rb'), content_type='text/html')
    html = (
        '<html><body style="font-family:sans-serif;padding:40px;">'
        '<h2>Frontend not built yet</h2>'
        '<p>Please build the Vue frontend first:</p>'
        '<code style="background:#f5f5f5;padding:10px;display:block;">'
        'cd frontend &amp;&amp; npm install &amp;&amp; npm run build<br>'
        'xcopy /e /i dist ..\\backend\\frontend_build</code>'
        '</body></html>'
    )
    return HttpResponseNotFound(html.encode('utf-8'), content_type='text/html; charset=utf-8')


def serve_frontend_or_index(request, path):
    """
    智能服务前端资源：
    1. 如果请求的文件实际存在于 FRONTEND_DIR → 返回该文件
    2. 否则 → 返回 index.html（Vue Router history 模式的 SPA 回退）
    这让 /upload、/manage 等前端路由都能正常工作
    """
    full_path = os.path.join(str(settings.FRONTEND_DIR), path)
    if path and os.path.exists(full_path) and os.path.isfile(full_path):
        return serve(request, path, document_root=str(settings.FRONTEND_DIR))
    # 文件不存在（如前端路由），回退到 SPA index.html
    return index(request)


def serve_media(request, path):
    """服务用户上传的文件"""
    return serve(request, path, document_root=str(settings.MEDIA_ROOT))
