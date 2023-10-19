"""
WSGI config for lalipo project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os
from pathlib import Path

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lalipo.settings')

if "CREDENTIALS_DIRECTORY" in os.environ:
    creds_dir = Path(os.environ["CREDENTIALS_DIRECTORY"])
    print(f"Loading credentials from {creds_dir}")
    for creds_file in creds_dir.iterdir():
        os.environ[creds_file.name] = creds_file.read_text()

application = get_wsgi_application()
