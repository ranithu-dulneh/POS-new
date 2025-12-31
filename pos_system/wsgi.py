"""
WSGI config for pos_system project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pos_system.settings")

application = get_wsgi_application()

# Vercel-specific: Auto-migrate if using local sqlite in tmp
# This is a hack to ensure the app works on Vercel without a real DB for demo purposes
if 'VERCEL' in os.environ and not os.environ.get('DATABASE_URL'):
    from django.core.management import call_command
    try:
        call_command('migrate')
    except Exception as e:
        print(f"Auto-migration failed: {e}")

app = application
