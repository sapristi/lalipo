#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
if "CREDENTIALS_DIRECTORY" in os.environ:
    creds_dir = Path(os.environ["CREDENTIALS_DIRECTORY"])
    print(f"Loading credentials from {creds_dir}")
    for creds_file in creds_dir.iterdir():
        os.environ[creds_file.name] = creds_file.read_text()


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lalipo.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
