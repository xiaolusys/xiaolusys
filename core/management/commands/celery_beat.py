from daemonextension import DaemonCommand
from django.core.management import call_command


class Command(DaemonCommand):
    def handle_daemon(self, *args, **options):
        params = {'WORKING_DIRECTORY': options['working_directory']}
        call_command('celerybeat', **params)

