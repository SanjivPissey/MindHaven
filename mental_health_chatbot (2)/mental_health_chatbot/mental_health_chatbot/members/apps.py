from django.apps import AppConfig

class MembersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'members'  # ✅ Ensure this matches your actual app name

    def ready(self):
        import os
        # Prevent the scheduler from running twice (once for the server, once for the auto-reloader)
        if os.environ.get('RUN_MAIN', None) != 'true':
            from . import scheduler
            scheduler.start()