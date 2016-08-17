import os

def setup_djagno_environ():
    if os.environ.get('TARGET') in ('production', 'django18'):
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shopmanager.production")

    elif os.environ.get('TARGET') in ('staging',):
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shopmanager.staging")

    else:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shopmanager.local_settings")