"""
WSGI config for food_health_app project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'food_health_app.settings')

application = get_wsgi_application()

# Automatically ensure database tables/migrations are up to date on deployment
try:
    import logging
    from django.core.management import call_command
    call_command('migrate', interactive=False)
except Exception as exc:
    import logging
    logging.getLogger(__name__).warning("Automatic startup migration notice: %s", exc)

