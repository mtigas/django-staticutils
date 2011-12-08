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
    help = "Purges all files from `VERSIONED_STATIC_ROOT` that are not "\
           "current versions of static files. (Files where the version "\
           "*matches* the source file's current version are not removed, "\
           "unless the `--all` flag is given.)"

    option_list = NoArgsCommand.option_list + (
        make_option('-n', '--dry-run', action='store_true', dest='dry_run',
            default=False, help="Do everything except modify the filesystem."),
        make_option('-i', '--ignore', action='append', default=[],
            dest='ignore_patterns', metavar='PATTERN',
            help="Ignore files or directories matching this glob-style "
                "pattern. Use multiple times to ignore more."),
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
        make_option('--no-default-ignore', action='store_false',
            dest='use_default_ignore_patterns', default=True,
            help="Don't ignore the common private glob-style patterns 'CVS', "
                "'.*' and '*~'."),
    )

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.deleted_files = []
        self.unmodified_files = []

        # Force storage to be a filesystem storage for VERSIONED_STATIC_ROOT.
        self.storage = get_storage_class(settings.STATICFILES_STORAGE)()
        self.versioned_storage = FileSystemStorage(location=settings.VERSIONED_STATIC_ROOT)

    def handle_noargs(self, **options):
        self.verbosity = int(options.get('verbosity', 1))

        ignore_patterns = options['ignore_patterns']
        if options['use_default_ignore_patterns']:
            ignore_patterns += ['CVS', '.*', '*~']
        ignore_patterns = list(set(ignore_patterns))

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

        # Get output filenames for up-to-date static files.
        self.valid_outpaths = set()
        if not options['all']:
            for finder in finders.get_finders():
                for path, storage in finder.list(ignore_patterns):
                    # Prefix the relative path if source storage contains it
                    if getattr(storage, 'prefix', None):
                        prefixed_path = os.path.join(storage.prefix, path)
                    else:
                        prefixed_path = path

                    current_version = get_file_version(path, storage)
                    current_outpath = get_versioned_path(
                        prefixed_path, current_version)

                    self.valid_outpaths.add(current_outpath)

        # Find everything currently in VERSIONED_STATIC_ROOT and remove
        # anything not in `self.valid_outpaths`
        def cleardirs(cd, subdirs, files):
            for d in subdirs:
                new_cd = os.path.join(cd, d)
                new_subdirs, new_files = self.versioned_storage.listdir(
                    os.path.join(cd, d)
                )
                cleardirs(new_cd, new_subdirs, new_files)
            for f in files:
                filepath = os.path.join(cd, f)
                if filepath not in self.valid_outpaths:
                    if options['dry_run']:
                        self.log(u"Pretending to delete '%s'" % filepath)
                    else:
                        self.log(u"Deleting '%s'" % filepath)
                        self.versioned_storage.delete(filepath)
                    self.deleted_files.append(filepath)
                else:
                    self.log(u"Skipping up-to-date file '%s'" % filepath)
                    self.unmodified_files.append(filepath)

        subdirs, files = self.versioned_storage.listdir("")
        cleardirs("", subdirs, files)

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
