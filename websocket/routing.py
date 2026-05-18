from django.urls import path, re_path

from . import consumers as print
from .consumers import RealtimeConsumer

websocket_urlpatterns = [
    path("ws/print/<str:room_name>/", print.PrintConsumer.as_asgi()),
    re_path(r"ws/realtime/(?P<table>\w+)/$", RealtimeConsumer.as_asgi()),
]
