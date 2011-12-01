import os
import sys
from optparse import make_option
from django.conf import settings
from django.contrib.staticfiles import finders
from django.contrib.staticfiles.management.commands import collectstatic
from django.core.files.storage import FileSystemStorage
from django.core.management.base import CommandError
from django.utils.encoding import smart_str
from staticutils.utils import file_version_hash, path_to_versioned_path

class Command(collectstatic.Command):
    help = "Collect static files from apps and other locations into "\
           "`HASHED_STATIC_ROOT` and adds a hash to each filename. (Used in "\
           "conjunction with the {% cachebust %} template tag.)"

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

    # Basically override collectstatic.__init__ by forcing storage to be a
    # FileSystemStorage with a destination of `HASHED_STATIC_ROOT` (instead
    # of `STATIC_ROOT`).
    def __init__(self, *args, **kwargs):
        super(collectstatic.Command, self).__init__(*args, **kwargs)
        self.copied_files = []
        self.symlinked_files = []
        self.unmodified_files = []
        self.storage = FileSystemStorage(location=settings.HASHED_STATIC_ROOT)
        try:
            self.storage.path('')
        except NotImplementedError:
            self.local = False
        else:
            self.local = True
        # Use ints for file times (ticket #14665)
        os.stat_float_times(False)

    # Same as original, except:
    #   * we modify the output filename to include the file's MD5 hash.
    #     (see "for finder in finders.get_finders():" loop, before "if symlink"
    #   * the log output uses `HASHED_STATIC_ROOT` instead
    def handle_noargs(self, **options):
        symlink = options['link']
        ignore_patterns = options['ignore_patterns']
        if options['use_default_ignore_patterns']:
            ignore_patterns += ['CVS', '.*', '*~']
        ignore_patterns = list(set(ignore_patterns))
        self.verbosity = int(options.get('verbosity', 1))

        if symlink:
            if sys.platform == 'win32':
                raise CommandError("Symlinking is not supported by this "
                                   "platform (%s)." % sys.platform)
            if not self.local:
                raise CommandError("Can't symlink to a remote destination.")

        # Warn before doing anything more.
        if options.get('interactive'):
            confirm = raw_input(u"""
You have requested to collect static files at the destination
location as specified in your settings file.

This will overwrite existing files.
Are you sure you want to do this?

Type 'yes' to continue, or 'no' to cancel: """)
            if confirm != 'yes':
                raise CommandError("Collecting static files cancelled.")

        for finder in finders.get_finders():
            for path, storage in finder.list(ignore_patterns):
                # Prefix the relative path if the source storage contains it
                if getattr(storage, 'prefix', None):
                    prefixed_path = os.path.join(storage.prefix, path)
                else:
                    prefixed_path = path

                # MODIFIED
                version = file_version_hash(path, storage)
                prefixed_path = path_to_versioned_path(prefixed_path, version)
                # /MODIFIED

                if symlink:
                    self.link_file(path, prefixed_path, storage, **options)
                else:
                    self.copy_file(path, prefixed_path, storage, **options)

        actual_count = len(self.copied_files) + len(self.symlinked_files)
        unmodified_count = len(self.unmodified_files)
        if self.verbosity >= 1:
            self.stdout.write(smart_str(u"\n%s static file%s %s to '%s'%s.\n"
                              % (actual_count, actual_count != 1 and 's' or '',
                                 symlink and 'symlinked' or 'copied',
                                 settings.HASHED_STATIC_ROOT,
                                 unmodified_count and ' (%s unmodified)'
                                 % unmodified_count or '')))
