#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import warnings
from pathlib import Path

# Supprimer les warnings GLib/GTK (WeasyPrint sur Windows)
os.environ['G_MESSAGES_DEBUG'] = ''
os.environ['GIO_EXTRA_MODULES'] = ''
os.environ['GDK_BACKEND'] = 'win32'

# Filtrer les warnings Python
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', message='.*GLib.*')


def main() -> None:
    """Run administrative tasks."""
    # Charger .env AVANT tout : garantit le bon settings module sans bricolage
    _env_path = Path(__file__).resolve().parent / '.env'
    if _env_path.exists():
        from dotenv import load_dotenv
        load_dotenv(_env_path, override=False)

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
    try:
        from django.core.management import execute_from_command_line  # type: ignore
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()