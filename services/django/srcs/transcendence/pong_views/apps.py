from django.apps import AppConfig

from django.db.models.signals import post_migrate
from .signals import post_migrate_handler

class PongViewsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pong_views'

    # def ready(self):
    #     post_migrate.connect(post_migrate_handler, sender=self)
    #     users = BaseUser.objects.all()
    #     for user in users:
    #         user.online = 0
    #         user.save()