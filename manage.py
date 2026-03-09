#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import webbrowser
import threading


def open_browser():
    webbrowser.open('http://127.0.0.1:8000/swagger/')


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Duel_Main.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    
    if len(sys.argv) >= 2 and sys.argv[1] == 'runserver' and os.environ.get('RUN_MAIN') == 'true':
        threading.Timer(1.5, open_browser).start()
    
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
