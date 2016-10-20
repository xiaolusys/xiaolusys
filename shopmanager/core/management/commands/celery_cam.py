from daemonextension import DaemonCommand
from django.core.management import call_command


class Command(DaemonCommand):
    def handle_daemon(self, *args, **options):
        options.pop('pidfile', None)
        call_command('celerycam', *args, **options)
