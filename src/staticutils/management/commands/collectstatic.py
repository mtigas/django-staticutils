from django.conf import settings
from django.contrib.staticfiles.management.commands import collectstatic
from django.core.management.base import CommandError, NoArgsCommand
from optparse import make_option

class Command(NoArgsCommand):
    help = collectstatic.Command.help
    option_list = collectstatic.Command.option_list + (
        make_option('--hashed-only',
            action='store_true',
            dest='hashed_only',
            default=False,
            help='Only collect static assets from `HASHED_STATIC_ROOT`. '\
                 'Cannot be used with `--plain`.'),
        make_option('--plain',
            action='store_true',
            dest='plain',
            default=False,
            help='Ignore `HASHED_STATIC_ROOT`. (Original behavior.) '\
                 'Cannot be used with `--hashed-only`.'),
    )

    def handle_noargs(self, hashed_only=False, plain=False, **options):
        if hashed_only and plain:
            raise CommandError(
                "--hashed-only and --plain cannot be used together."
            )

        # Call regular `collectstatic`
        collectstatic.Command().execute(**options)
