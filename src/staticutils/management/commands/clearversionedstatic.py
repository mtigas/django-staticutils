from django.core.files.storage import FileSystemStorage
from django.core.management.base import CommandError, NoArgsCommand
from staticutils.versioning import get_file_version, get_versioned_path
from django.contrib.staticfiles import finders
import os
from django.utils.encoding import smart_str
from optparse import make_option
from glob import iglob
from django.conf import settings
from django.core.files.storage import get_storage_class


class Command(NoArgsCommand):
    help = "Purges *old* versioned static files from `VERSIONED_STATIC_ROOT`. "\
           "(Files where the version *matches* the source file's current version "\
           "are not removed, unless the `--all` flag is given.)"

    option_list = NoArgsCommand.option_list + (
        make_option('-n', '--dry-run', action='store_true', dest='dry_run',
            default=False, help="Do everything except modify the filesystem."),
        make_option('--all',
            action='store_true',
            dest='all',
            default=False,
            help='Removes *everything* from `VERSIONED_STATIC_ROOT`, not just '\
                 'old versions of static files.'),
        make_option('--noinput',
            action='store_true',
            dest='interactive',
            default=False,
            help='Does not prompt for confirmation when deleting.'),
    )

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.deleted_files = []
        self.unmodified_files = []

        # Force storage to be a filesystem storage for VERSIONED_STATIC_ROOT.
        self.storage = get_storage_class(settings.STATICFILES_STORAGE)()
        self.versioned_storage = FileSystemStorage(location=settings.VERSIONED_STATIC_ROOT)
        try:
            self.storage.path('')
        except NotImplementedError:
            self.local = False
        else:
            self.local = True

    def handle_noargs(self, **options):
        self.verbosity = int(options.get('verbosity', 1))

        # Warn before doing anything more.
        if options.get('interactive'):
            confirm = raw_input(u"""
You have requested to delete versioned files at the destination
location as specified in your settings file.

This will remove existing files.
Are you sure you want to do this?

Type 'yes' to continue, or 'no' to cancel: """)
            if confirm != 'yes':
                raise CommandError("Collecting static files cancelled.")

        for finder in finders.get_finders():
            for path, storage in finder.list(['CVS', '.*', '*~']):
                # Prefix the relative path if the source storage contains it
                if getattr(storage, 'prefix', None):
                    prefixed_path = os.path.join(storage.prefix, path)
                else:
                    prefixed_path = path
                self.remove_old_versions(
                    path, prefixed_path, storage, **options
                )

        actual_count = len(self.deleted_files)
        unmodified_count = len(self.unmodified_files)
        if self.verbosity >= 1:
            self.stdout.write(smart_str(u"\n%s versioned file%s %s%s.\n"
                              % (actual_count, actual_count != 1 and 's' or '',
                                 'deleted',
                                 unmodified_count and ' (%s unmodified)'
                                 % unmodified_count or '')))


    def log(self, msg, level=2):
        """
        Small log helper
        """
        msg = smart_str(msg)
        if not msg.endswith("\n"):
            msg += "\n"
        if self.verbosity >= level:
            self.stdout.write(msg)

    def remove_old_versions(self, path, prefixed_path, source_storage, **kwargs):
        # For iglob matching to work, we actually need the full path
        # of the output file.
        outpath = os.path.join(settings.VERSIONED_STATIC_ROOT, prefixed_path)

        current_version = get_file_version(path, source_storage)
        current_outpath = get_versioned_path(outpath, current_version)

        # Match any possible version of the output file.
        for matching_path in iglob(get_versioned_path(outpath, "*")):
            # Remove VERSIONED_STATIC_ROOT just for output log, etc.
            rel_matching_path = matching_path.replace(
                settings.VERSIONED_STATIC_ROOT, "", 1
            )[1:]
            if kwargs['all'] or (matching_path != current_outpath):
                self.deleted_files.append(matching_path)
                if kwargs['dry_run']:
                    self.log(u"Pretending to delete '%s' (Current is '%s')" % (
                        rel_matching_path, current_version
                    ))
                else:
                    self.log(u"Deleting '%s' (Current is '%s')" % (
                        rel_matching_path, current_version
                    ))
                    os.unlink(matching_path)
                    self.versioned_storage.delete(matching_path)
            else:
                self.unmodified_files.append(matching_path)
                self.log(u"Skipping '%s'. (Current version.)" % rel_matching_path)
