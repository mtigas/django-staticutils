import os
import sys
from itertools import chain
from optparse import make_option
from django.contrib.staticfiles import finders
from django.utils.encoding import smart_str
from django.conf import settings
from django.contrib.staticfiles.management.commands import collectstatic
from django.core.management.base import CommandError
from staticutils.finders import HashedStaticRootFinder


class Command(collectstatic.Command):
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

        if hashed_only:
            # Only use our HashedStaticRootFinder and ignore original behavior.
            finders_to_use = [HashedStaticRootFinder(), ]
        elif plain:
            # The original behavior only.
            finders_to_use = finders.get_finders()
        else:
            # Original behavior + HASHED_STATIC_ROOT. Use chain since
            # `get_finders` is an iterable (so instantiation is delayed until
            # the objects are actually needed).
            finders_to_use = chain(
                finders.get_finders(),
                (HashedStaticRootFinder(),)
            )

        ##### Original handle_noargs #####
        # Have to copy the whole handle_noargs bit here because it dynamically
        # uses `django.contrib.staticfiles.finders` at runtime, which we can't
        # override unless we override the runtime behavior itself.
        #
        # Only modified line is "for finder in finders_to_use"
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

        for finder in finders_to_use:  # MODIFIED
            for path, storage in finder.list(ignore_patterns):
                # Prefix the relative path if the source storage contains it
                if getattr(storage, 'prefix', None):
                    prefixed_path = os.path.join(storage.prefix, path)
                else:
                    prefixed_path = path
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
                                 settings.STATIC_ROOT,
                                 unmodified_count and ' (%s unmodified)'
                                 % unmodified_count or '')))
        ##### /Original handle_noargs #####
