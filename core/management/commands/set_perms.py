# from daemonextension import DaemonCommand
from django.core.management import call_command
from shopmanager.permissions import update_permissions
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    def handle(self, *args, **options):
        update_permissions()