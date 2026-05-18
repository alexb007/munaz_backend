"""
ASGI entrypoint. Configures Django and then runs the application
defined in the ASGI_APPLICATION setting.
"""

import os

import django
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

import websocket

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "munaz_back.settings")
django.setup()
django_asgi_app = get_asgi_application()

from channels_auth_token_middlewares.middleware import SimpleJWTAuthTokenMiddleware

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            SimpleJWTAuthTokenMiddleware(
                URLRouter(websocket.routing.websocket_urlpatterns),
                keyword="JWT",
            )
        )
    ),
})
