from django.core.management.base import NoArgsCommand
from optparse import make_option


class Command(NoArgsCommand):
    help = "Collect static files from apps and other locations into "\
           "`HASHED_STATIC_ROOT` and adds a hash to each filename. (Used in "\
           "conjunction with the {% cachebust %} template tag.)"

    option_list = NoArgsCommand.option_list + (
        make_option('-l', '--link',
            action='store_true',
            dest='link',
            default=False,
            help='Create a symbolic link to each file instead of copying.'),
    )

    def handle_noargs(self, **options):
        pass
