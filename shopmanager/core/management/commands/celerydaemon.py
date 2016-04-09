from daemonextension import DaemonCommand
from django.conf import settings
from django.core.management import call_command


class Command(DaemonCommand):
    
    def handle_daemon(self, *args, **options):

        call_command('celeryd')