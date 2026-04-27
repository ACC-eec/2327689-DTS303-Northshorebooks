from django.contrib.staticfiles.views import serve
from django.http import HttpResponse
import os

def staticfiles_serve(request, path, **kwargs):
    response = serve(request, path, **kwargs)
    # Ensure CSS files have correct MIME type
    if path.endswith('.css'):
        response['Content-Type'] = 'text/css; charset=utf-8'
    elif path.endswith('.js'):
        response['Content-Type'] = 'application/javascript; charset=utf-8'
    elif path.endswith('.svg'):
        response['Content-Type'] = 'image/svg+xml; charset=utf-8'
    return response
