from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class WebsocketConfig(AppConfig):
    name = 'websocket'
    verbose_name = _('Сокеты')

