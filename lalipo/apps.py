
from django.apps import AppConfig


class Lalipo(AppConfig):
    name = "lalipo"

    def ready(self):
        import lalipo.signals
