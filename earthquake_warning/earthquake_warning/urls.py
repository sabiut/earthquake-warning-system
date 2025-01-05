# earthquake_warning/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from earthquake_app.routing import websocket_urlpatterns

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('earthquake_app.urls')),  # Include your app's regular views
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Add ASGI WebSockets routing
application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": URLRouter(websocket_urlpatterns),
})
