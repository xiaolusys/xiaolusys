from django.core.management.commands.runserver import BaseRunserverCommand
from optparse import make_option
from django.core.servers.basehttp import AdminMediaHandler

class Command(BaseRunserverCommand):
    option_list = BaseRunserverCommand.option_list + (
        make_option('--adminmedia', dest='admin_media_path', default='',
            help='Specifies the directory from which to serve admin media.'),
    )

    """
    Change the runserver default port to 9000. The method can be generically applied if
    the default port needs to be changed.
    """
    def handle(self, addrport="9000", *args, **options):
        super(Command, self).handle(addrport, *args, **options)

    def get_handler(self, *args, **options):
        """
        Serves admin media like old-school (deprecation pending).
        """

        handler = super(Command, self).get_handler(*args, **options)
        return AdminMediaHandler(handler, options.get('admin_media_path', ''))