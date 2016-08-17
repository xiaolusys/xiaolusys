#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":

    if os.environ.get('TARGET') in ('production', 'django18'):
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shopmanager.production")

    elif os.environ.get('TARGET') in ('staging',):
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shopmanager.staging")

    else:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shopmanager.local_settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
