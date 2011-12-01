from django.conf import settings
from django.contrib.staticfiles.finders import FileSystemFinder
from django.core.files.storage import FileSystemStorage
from django.utils.datastructures import SortedDict


class HashedStaticRootFinder(FileSystemFinder):
    """
    A hackish version of `FileSystemFinder` that returns resources in
    `settings.HASHED_STATIC_ROOT`.
    """
    def __init__(self, apps=None, *args, **kwargs):
        # List of locations with static files
        self.locations = [('', settings.HASHED_STATIC_ROOT), ]
        # Maps dir paths to an appropriate storage instance
        self.storages = SortedDict()

        for prefix, root in self.locations:
            filesystem_storage = FileSystemStorage(location=root)
            filesystem_storage.prefix = prefix
            self.storages[root] = filesystem_storage
        super(FileSystemFinder, self).__init__(*args, **kwargs)
